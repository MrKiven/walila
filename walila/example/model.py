# -*- coding: utf-8 -*-

from sqlalchemy import (
    Column,
    Integer,
    String,
    SmallInteger
)

from walila.settings import settings
from walila.db import db_manager, model_base


class DBSetting(object):
    __master = "mysql+pymysql://root@localhost:3306/walila?charset=utf8"
    __slave = "mysql+pymysql://root@localhost:3306/walila?charset=utf8"

    DB_SETTINGS = {
        "walila": {
            "urls": {
                "master": __master,
                "slave": __slave
            }
        }
    }

settings.from_object(DBSetting)

ModelBase = model_base()
db_manager.create_sessions()
DBSession = db_manager.get_session('walila')


class TODOList(ModelBase):

    __tablename__ = 'todo'

    id = Column(Integer, primary_key=True)
    title = Column(String, default='')
    is_done = Column(SmallInteger, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'is_done': self.is_done
        }

    @classmethod
    def get(cls, todo_id):
        session = DBSession()
        todo = session.query(cls).get(todo_id)
        if todo:
            return todo.to_dict()

    @classmethod
    def add(cls, title):
        todo = cls(title=title)
        session = DBSession()
        session.add(todo)
        session.commit()
