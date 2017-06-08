### Walila - Awesome toolkit for internal

![walila](resource/walila.jpg)


### Install

```shell
pip install walila
```

`walila --help` for more detail.


### Sample project

```
hello
├── app.yaml
├── requirements.txt
├── tests
│   ├── __init__.py
│   └── conftest.py
└── world
    ├── __init__.py
    ├── app.py
    └── settings.py
```

### Components

1. db manager
2. settings wrapper
3. hook wrapper
4. rabbitmq wrapper


### Try async task

```
$ celery -A walila.example.task worker -l INFO -Q default -c 10
```

```
$ python test.py 10
```
