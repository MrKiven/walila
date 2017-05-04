### Walila - Awesome toolkit for internal

![walila](resource/walila.jpg)

Walila(瓦莉拉) 是艾泽拉斯最厉害的刺客之一.


### 组件

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
