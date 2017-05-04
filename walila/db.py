# -*- coding: utf-8 -*-

import functools
import random
import uuid
import logging

import gevent
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy import types
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import (
    Executable, ClauseElement, Insert, _literal_as_text)

from .settings import settings


def patch_column_type_checker():
    def coerce_compared_value(self, op, value):
        return self

    def predicate_type(types):
        def wrapper(func):
            @functools.wraps(func)
            def bind_processor(*args, **kwds):
                processor = func(*args, **kwds)
                if processor is None:
                    def validator(value):
                        if not isinstance(value, types):
                            raise TypeError("ONLY IN DEV: Column type defined"
                                            " in model: %s, Got: %s"
                                            % (types, type(value)))
                        return value
                else:
                    def validator(value):
                        res = processor(value)
                        if not isinstance(res, types):
                            raise TypeError("ONLY IN DEV: Column type defined"
                                            " in model: %s, Got: %s"
                                            % (types, type(value)))
                        return res
                return validator
            return bind_processor
        return wrapper

    Integer.coerce_compared_value = coerce_compared_value
    Integer.bind_processor = predicate_type((int, long))(
        Integer.bind_processor
        )

    String.coerce_compared_value = coerce_compared_value
    String.bind_processor = predicate_type(basestring)(String.bind_processor)


class StrongInteger(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if not isinstance(value, (int, long)):
            value = int(value)
        return value


logger = logging.getLogger(__name__)


class TaskHashMixin(object):
    @classmethod
    def gen_task_hash(cls, conn, task_name, task_args):
        raise NotImplementedError


class UpsertMixin(object):
    @classmethod
    def upsert(cls):
        """Build :class:`zeus_core.db.Upsert` statement.

        Example::

            class Foo(ModelBase, UpsertMixin):
                @classmethod
                def ensure(cls, name):
                    with DBSession() as db:
                        db.execute(cls.upsert().values(name=name))
        """
        return Upsert(cls.__table__)


class Explain(Executable, ClauseElement):
    def __init__(self, stmt, analyze=False):
        self.statement = _literal_as_text(stmt)
        self.analyze = analyze


class Upsert(Insert):
    pass


@compiles(Explain, 'mysql')
def mysql_explain(element, compiler, **kw):
    text = 'EXPLAIN '
    if element.analyze:
        text += 'EXTENDED '
    text += compiler.process(element.statement)
    return text


@compiles(Upsert, 'mysql')
def mysql_upsert(insert_stmt, compiler, **kwargs):
    # A modified version of https://gist.github.com/timtadh/7811458.
    # The license (3-Clause BSD) is in the repository root.
    parameters = insert_stmt.parameters
    if insert_stmt._has_multi_parameters:
        parameters = parameters[0]
    keys = list(parameters or {})
    pk = insert_stmt.table.primary_key
    auto = None
    if (len(pk.columns) == 1 and
            isinstance(pk.columns.values()[0].type, Integer) and
            pk.columns.values()[0].autoincrement):
        auto = pk.columns.keys()[0]
        if auto in keys:
            keys.remove(auto)
    insert = compiler.visit_insert(insert_stmt, **kwargs)
    ondup = 'ON DUPLICATE KEY UPDATE'
    updates = ', '.join(
        '%s = VALUES(%s)' % (c.name, c.name)
        for c in insert_stmt.table.columns
        if c.name in keys
    )
    if auto is not None:
        last_id = '%s = LAST_INSERT_ID(%s)' % (auto, auto)
        if updates:
            updates = ', '.join((last_id, updates))
        else:
            updates = last_id
    upsert = ' '.join((insert, ondup, updates))
    return upsert


def close_connections(engines, transactions):
    if engines and transactions:
        for engine in engines:
            for parent in transactions:
                conn = parent._connections.get(engine)
                if conn:
                    conn = conn[0]
                    conn.invalidate()


class RoutingSession(Session):
    _name = None
    CLOSE_ON_EXIT = True

    def __init__(self, engines, *args, **kwds):
        super(RoutingSession, self).__init__(*args, **kwds)
        self.engines = engines
        self.slave_engines = [e for role, e in engines.items()
                              if role != 'master']
        assert self.slave_engines, ValueError("DB slave configs is wrong!")
        self._close_on_exit = self.CLOSE_ON_EXIT

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_val is None:
                self.flush()
                self.commit()
            elif isinstance(exc_val, SQLAlchemyError):
                self.rollback()
        except SQLAlchemyError:
            self.rollback()
            raise
        finally:
            if self._close_on_exit:
                self.close()
            self._close_on_exit = self.CLOSE_ON_EXIT

    def close_on_exit(self, value):
        self._close_on_exit = bool(value)
        return self

    def explain(self, query, analyze=False):
        """EXPLAIN for mysql
        :param query: `Query` Object
        :param analyze: if add `EXTENDED` before query statement
        """
        plan = self.execute(Explain(query, analyze)).fetchall()
        for item in plan:
            for k, v in item.items():
                print '%s: %s' % (k, v)

    def get_bind(self, mapper=None, clause=None):
        if self._name:
            return self.engines[self._name]
        elif self._flushing:
            return self.engines['master']
        else:
            return random.choice(self.slave_engines)

    def using_bind(self, name):
        self._name = name
        return self

    def rollback(self):
        with gevent.Timeout(5):
            super(RoutingSession, self).rollback()

    def close(self):
        current_transactions = tuple()
        if self.transaction is not None:
            current_transactions = self.transaction._iterate_parents()
        try:
            with gevent.Timeout(5):
                super(RoutingSession, self).close()
        # pylint: disable=E0712
        except gevent.Timeout:
            # pylint: enable=E0712
            close_connections(self.engines.itervalues(), current_transactions)
            raise


def patch_engine(engine):
    pool = engine.pool
    pool._origin_recyle = pool._recycle
    del pool._recycle
    setattr(pool.__class__, '_recycle', RecycleField())
    return engine


def create_engine(*args, **kwds):
    engine = patch_engine(sqlalchemy_create_engine(*args, **kwds))
    return engine


def make_session(engines, force_scope=False, info=None):
    session = scoped_session(
        sessionmaker(
            class_=RoutingSession,
            expire_on_commit=False,
            engines=engines,
            info=info or {"name": uuid.uuid4().hex},
        ),
        scopefunc=None
    )
    return session


def gen_commit_deco(session_factory, raise_exc, error_code):
    def decorated(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                with session_factory():
                    return func(*args, **kwargs)
            except SQLAlchemyError as e:
                raise_exc(error_code, repr(e))
        return wrapper
    return decorated


class ModelMeta(DeclarativeMeta):
    def __new__(self, name, bases, attrs):
        cls = DeclarativeMeta.__new__(self, name, bases, attrs)

        # TODO: :class: `CacheMixinBase
        from .cache import CacheMixinBase
        for base in bases:
            if issubclass(base, CacheMixinBase) and hasattr(cls, "_hook"):
                cls._hook.add(cls)
                break
        return cls


def model_base(cls=object):
    """Construct a base class for declarative class definitions.

    :param cls:
      Atype to use as the base for the generated declarative base class.
      Defaults to :class:`object`. May be a class or tuple of classes.
    """
    return declarative_base(cls=cls, metaclass=ModelMeta)


class RecycleField(object):
    def __get__(self, instance, klass):
        if instance is not None:
            return int(random.uniform(0.75, 1) * instance._origin_recyle)
        raise AttributeError


class DBManager(object):
    def __init__(self):
        self.loaded = False  # only create session once
        self.session_map = {}

    def create_sessions(self):
        if not self.loaded:
            if not settings.DB_SETTINGS:
                raise ValueError('DB_SETTINGS is empty, check it')
            for db, db_configs in settings.DB_SETTINGS.iteritems():
                self.add_session(db, db_configs)
            self.loaded = True

    def get_session(self, name):
        try:
            return self.session_map[name]
        except KeyError:
            raise KeyError(
                '`%s` session not created, check `DB_SETTINGS`' % name)

    def add_session(self, name, config):
        if name in self.session_map:
            raise ValueError("Duplicate session name {},"
                             "please check your config".format(name))
        session = self._make_session(name, config)
        self.session_map[name] = session
        return session

    @classmethod
    def _make_session(cls, db, config):
        urls = config['urls']
        for name, url in urls.iteritems():
            assert url, "Url configured not properly for %s:%s" % (db, name)
        pool_size = config.get('pool_size', settings.DB_POOL_SIZE)
        max_overflow = config.get(
            'max_overflow', settings.DB_MAX_OVERFLOW)
        pool_recycle = settings.DB_POOL_RECYCLE
        engines = {
            role: cls.create_engine(dsn,
                                    pool_size=pool_size,
                                    max_overflow=max_overflow,
                                    pool_recycle=pool_recycle,
                                    execution_options={'role': role})
            for role, dsn in urls.iteritems()
        }
        return make_session(engines, info={"name": db})

    def close_sessions(self, should_close_connection=False):
        dbsessions = self.session_map
        for dbsession in dbsessions.itervalues():
            if should_close_connection:
                session = dbsession()
                if session.transaction is not None:
                    close_connections(session.engines.itervalues(),
                                      session.transaction._iterate_parents())
            try:
                dbsession.remove()
            except:
                logger.exception("Error closing session")

    @classmethod
    def create_engine(cls, *args, **kwds):
        engine = patch_engine(sqlalchemy_create_engine(*args, **kwds))
        return engine


db_manager = DBManager()
