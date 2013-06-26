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

from yweb.quemail import QueMail
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

    _cur_unique_id = 0

    _supported_languages = {}
    _supported_languages_list = None

    _quemail_instance = None

    def __init__(self):

        # Clc connect
        self.clcstream = None

        # SQLAlchemy connect
        self.db = orm.db

        # TODO: TEST db connect

        site_handlers = get_handlers()

        self.init_runtime_data()

        tornado.web.Application.__init__(
            self, site_handlers, **tornado_settings )


    @property
    def supported_languages(self):
        if not self._supported_languages:
            self._supported_languages = self.get_supported_languages()

        return self._supported_languages

    @property
    def supported_languages_list(self):
        if not self._supported_languages_list:
            self._supported_languages_list = self.get_supported_languages().values()

        return self._supported_languages_list


    def get_supported_languages(self):

        supported_languages = {}

        from app.language.models import Language
        for codename, x in self.settings["LANGUAGES"]:
            L = self.db.query(Language).filter_by(
                codename = codename ).first()
            if not L: continue
            supported_languages[codename] = L

        return supported_languages


    def get_unique_id(self):
        self._cur_unique_id += 1
        return self._cur_unique_id


    def get_quemail(self):

        if not self._quemail_instance:

            # TODO:
            smtp_server = SiteConfig.get(
                self.db, 'notice.smtp.server', None)
            smtp_port = int(SiteConfig.get(
                    self.db, 'notice.smtp.port', 0 ))
            smtp_username = SiteConfig.get(
                self.db, 'notice.smtp.username', None)
            smtp_password = SiteConfig.get(
                self.db, 'notice.smtp.password', None)

            if ( not smtp_server or
                 not smtp_port or
                 not smtp_username or
                 not smtp_password ):

                from yweb.quemail import DummyMail
                return DummyMail.get_instance()

            qm = QueMail.get_instance()
            qm.init( smtp_server, smtp_username, smtp_password,
                     smtp_port = smtp_port )

            qm.start()
            self._quemail_instance = qm

        return self._quemail_instance


    def init_runtime_data(self):

        # domain
        _domain = self.db.query(SiteConfig).filter_by(
            key = 'domain' ).first()
        if _domain:
            domain = json.loads(_domain.value)
            settings.runtime_data['domain'] = domain



def exit_handler(_signal, frame):

    if _signal == signal.SIGINT:
        print " ... You Pressed CTL+C, exit ... "

    elif _signal == signal.SIGHUP:
        print " ... get SIGHUP, exit ... "

    if _signal == signal.SIGTERM:
        print " ... get SIGTERM, exit ... "

    # TODO: exit
    #orm.db.dispose()

    # TODO: quit email
    try:
        from yweb.quemail import QueMail
        qm = QueMail.get_instance()
        qm.end()
    except RuntimeError:
        pass


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

    from yweb.utils.processwatcher import ProcessWatcher
    ProcessWatcher()


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
