#!/usr/bin/env python
# coding: utf-8

import os
import json
import signal
import logging

import sys
reload(sys)
sys.setdefaultencoding('utf8') 

import settings

# TODO: i18n is too ugly yet
import __builtin__
__builtin__.__dict__['_'] = lambda s: s

import tornado
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.httpserver import HTTPServer

from app.site.models import SiteConfig

from lycustom import NotFoundHandler
import app.home.views as home_views
def get_handlers():

    handlers = []

    for m in settings.app:
        exec "from %s.urls import handlers as urls" % m
        try:
            exec "from %s.urls import handlers as urls" % m
            handlers.extend(urls)
        except ImportError, e:
            logging.debug('import handlers from %s.urls failed: %s' % (m, e))

    handlers.extend([
#            (r'/([^/ ]+)', home_views.GlobalEntry ),
            (r'/404.html', NotFoundHandler),
            (r'/(.*)', NotFoundHandler),
            ])

    return handlers


from tornado.options import define, options
define("port", default=8888, help="given port", type=int)

from yweb import orm


tornado_settings = {
    'cookie_secret': 'MTMyNTMwNDc3OC40MjA3NjgKCg==',
    'session_secret': 'gAJ9cQAoVQZsb2NhbGVxAVUFemhfQ05xAl',
    'xsrf_cookies': True,
    'login_url': '/login',
    'no_permission_url': '/no_permission',
    'no_resource_url': '/no_resource',
    'static_path': settings.STATIC_PATH,
    'template_path': settings.TEMPLATE_DIR,
    'gzip': True,
    'debug': True,

    # Global settings about LuoYun System
    'appliance_top_dir': settings.appliance_top_dir,
    'appliance_top_url': settings.appliance_top_url,
    'control_server_ip': settings.control_server_ip,
    'control_server_port': settings.control_server_port,

    'THEME': settings.THEME,
    'THEME_URL': settings.THEME_URL,
    'STATIC_URL': settings.STATIC_URL,
    'LANGUAGES': settings.LANGUAGES,

    'LYJOB_ACTION': settings.LYJOB_ACTION,
}


class Application(tornado.web.Application):

    _clcsock = None
    _clcstream = None

    def __init__(self):

        # SQLAlchemy connect
        self.dbsession = orm.create_session()

        # TODO: TEST db connect

        site_handlers = get_handlers()
        self.init_runtime_data()

        tornado.web.Application.__init__(
            self, site_handlers, **tornado_settings )


    @property
    def clcstream(self):
        if not self._clcstream and self.clcsock:
            from lyc.handler import MSGStream
            self._clcstream = MSGStream(self.clcsock)
        return self._clcstream

    @property
    def clcsock(self):
        if self._clcsock:
            return self._clcsock

        host = '127.0.0.1'
        port = 1368

        ssl_options = {'ca_certs': self._get_ca_certs(host, port)}

        from lyc.netutil import connect_to_server
        self._clcsock = connect_to_server(host, port, ssl_options)

        # TODO: auth

        return self._clcsock


    def _get_ca_certs(self, host, port):
        ca_path = os.path.join('/tmp', 'ca.pem')
        if os.path.exists(ca_path):
            logging.debug('%s exists, use it as certfile', ca_path)
            return ca_path

        try:
            import ssl
            ca = ssl.get_server_certificate((host, port))
            logging.debug('get_server_certificate from %s:%s success.', host, port)
        except Exception, e:
            logging.error('get_server_certificate failed: %s', e)
            return

        f = open(ca_path, 'w')
        f.write(ca)
        f.close()
        return ca_path

    def init_runtime_data(self):
        db = self.dbsession()
        domain = SiteConfig.get(db, 'domain', '')
        settings.runtime_data['domain'] = json.loads(domain)



def exit_handler(_signal, frame):

    if _signal == signal.SIGINT:
        print " ... You Pressed CTL+C, exit ... "

    elif _signal == signal.SIGHUP:
        print " ... get SIGHUP, exit ... "

    if _signal == signal.SIGTERM:
        print " ... get SIGTERM, exit ... "

    sys.exit(1)


from tornado.options import parse_command_line
from tornado.locale import load_gettext_translations, \
    set_default_locale

from tornado.netutil import bind_sockets

def main():

    # options
    parse_command_line()

    # Locale
    load_gettext_translations(settings.I18N_PATH, "luoyun")
    set_default_locale('zh_CN')

    logging.info("starting torando web server")

    if settings.IPV4_ONLY:
        import socket
        sockets = bind_sockets(options.port, family=socket.AF_INET)
    else:
        sockets = bind_sockets(options.port)

    if not settings.DEBUG:
        import tornado.process
        tornado.process.fork_processes(0)

    application = Application()
    server = HTTPServer(application, xheaders=True)
    server.add_sockets(sockets)
    IOLoop.instance().start()



if __name__ == "__main__":

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGHUP, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    try:
        main()
    finally:
        pass
