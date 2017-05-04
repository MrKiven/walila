# -*- coding: utf-8 -*-


from gunicorn.app.wsgiapp import WSGIApplication

from walila.config import load_app_config
from . import hooks

class SetAppMixin(object):

    def _setup(self, config, opts):
        self.cfg.set('default_proc_name', config.app_name)
        self.cfg.set('worker_class', config.worker_class)
        self.cfg.set('worker_connections', config.worker_connections)
        self.cfg.set('loglevel', 'info')
        self.cfg.set('graceful_timeout', 3)
        self.cfg.set('timeout', config.timeout)
        self.cfg.set('bind', config.get_app_binds())
        self.cfg.set('workers', config.get_app_n_workers())


class WalilaWsgiApp(SetAppMixin, WSGIApplication):

    def init(self, parser, opts, args):
        app_config = load_app_config()
        self.app_uri = app_config.app_uri
        args = [self.app_uri]
        self._setup(app_config, opts)
        self.install_hooks()
        super(WalilaWsgiApp, self).init(parser, opts, args)

    def install_hooks(self):
        self.cfg.set('post_fork', hooks.post_fork)
        self.cfg.set('accesslog', '-')
        self.cfg.set('errorlog', '-')
