# -*- coding: utf-8 -*-

from walila.hook import define_hook, hook_registry


@define_hook(event="before_api_called")
def hello():
    return 'hello world'

hook = hello


def test_define_hook():
    assert hello.event == 'before_api_called'
    assert hello.func() == "hello world" == hello() == hook()
    assert str(hook) == "<Hook event='before_api_called' func='hello'>"


def test_hook_registry():

    assert hook_registry._registry == {}

    hook_registry.register(hook)
    assert hook_registry._registry == {'before_api_called': [hook.func]}
    assert hook_registry.on_before_api_called() == ['hello world']

    hook_registry.clear()
    result = []

    @define_hook(event='h')
    def h():
        result.append('h')

    @define_hook(event='h')
    def e():
        result.append('e')

    @define_hook(event='h')
    def l():
        result.append('l')

    hook_registry.register(h)
    hook_registry.register(e)
    hook_registry.register(l)

    assert hook_registry._registry == {'h': [h.func, e.func, l.func]}

    hook_registry.on_h()
    assert result == ['h', 'e', 'l']
