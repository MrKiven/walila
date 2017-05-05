# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)


def hello():
    return 'Hello world!\n'

app.add_url_rule('/hello', 'hello', hello)

