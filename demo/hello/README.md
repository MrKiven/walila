### Walila demo app


##### Startup application

```shell
walila serve
```

##### Startup celery worker(consumer)

```shell
celery -A world.tasks worker -l INFO -E -Q default -c 10
```


##### Try to send a task

```shell
curl localhost:8010/tasks/my_task
```
