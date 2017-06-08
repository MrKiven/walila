# -*- coding: utf-8 -*-

import json
import importlib

from sqlalchemy import (
    String,
    Column,
    Integer,
    Text,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base


# model base
Model = declarative_base()


class FailedTask(Model):

    __tablename__ = 'FailedTask'

    name = Column(String(125), nullable=False, index=True)
    full_name = Column(Text, nullable=False)
    args = Column(Text)
    kwargs = Column(Text)
    exception_class = Column(Text, nullable=False)
    exception_msg = Column(Text, nullable=False)
    traceback = Column(Text)
    task_id = Column(String(36), nullable=False)
    failures = Column(Integer, nullable=False, default=1)
    need_retry = Column(Boolean, nullable=False, default=True)

    def retry_and_delete(self, inline=False):
        """Retry task and delete if success."""
        mod_name, func_name = self.full_name.rsplit('.', 1)
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)

        args = json.loads(self.args) if self.args else ()
        kwargs = json.loads(self.kwargs) if self.kwargs else {}

        if inline:
            res = func(*args, **kwargs)
            self.delete()
            return res

        self.delete()
        from .queue.async import task_manager
        return task_manager.apply_async(func_name, *args, **kwargs)

    @classmethod
    def get_all_need_retry(cls):
        """Get all need retry tasks"""
        return cls.query.filter(cls.need_retry.is_(True)).all()

    def delete(self):
        """
        with DBSession() as session:
            session.delete(self)
        """

    @classmethod
    def get_task(cls, full_name, args, kwargs, exception_class, exception_msg):
        return cls.query.filter(
            cls.full_name == full_name, cls.args == args, cls.kwargs == kwargs,
            cls.exception_class == exception_class,
            cls.exception_msg == exception_msg).first()
