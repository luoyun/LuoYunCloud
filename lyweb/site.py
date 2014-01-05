#!/usr/bin/env python
# coding: utf-8

import os
import signal
import logging

import sys
reload(sys)
sys.setdefaultencoding('utf8') 

import settings

# TODO: i18n is too ugly yet
import __builtin__
__builtin__.__dict__['_'] = lambda s: s

from tornado.ioloop import IOLoop, PeriodicCallback
import tornado.web

from urls import tornado_settings as app_settings
from urls import handlers as app_handlers

from tornado.options import define, options
define("port", default=8888, help="given port", type=int)

import lyorm


class Application(tornado.web.Application):

    _cur_unique_id = 0

    _supported_languages = {}
    _supported_languages_list = None

    def __init__(self):

        # Clc connect
        self.clcstream = None
        # SQLAlchemy connect
        self.db2 = lyorm.dbsession
        self.db = self.db2

        # TEST db connect
        try:
            from sqlalchemy.exc import OperationalError, ProgrammingError
            from tool.network import set_network_pool
            set_network_pool(self.db2)

            # Normal web server
            return tornado.web.Application.__init__(
                self, app_handlers, **app_settings )

        except OperationalError, msg:
            # DB connect error, show the install step
            logging.warning('OperationalError: %s' % msg)
        except ProgrammingError, msg:
            logging.warning('ProgrammingError: %s' % msg)
            # TODO
            import manage
            manage.syncdb()
            manage.i18n()

        except Exception, msg:
            print 'A error : %s !!!' % msg
            pass

        # This is error handlers
        from app.install.urls import handlers as install_handlers
        tornado.web.Application.__init__(self, install_handlers, **app_settings)

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


def exit_handler(_signal, frame):

    if _signal == signal.SIGINT:
        print " ... You Pressed CTL+C, exit ... "

    elif _signal == signal.SIGHUP:
        print " ... get SIGHUP, exit ... "

    if _signal == signal.SIGTERM:
        print " ... get SIGTERM, exit ... "

    # TODO: exit
    lyorm.dbengine.dispose()

    sys.exit(1)


def main():

    # options
    tornado.options.parse_command_line()

    # Locale
    tornado.locale.load_gettext_translations(settings.I18N_PATH, "luoyun")
    tornado.locale.set_default_locale('zh_CN')

    logging.info("starting torando web server")

    # Start listen
    Application().listen(options.port, xheaders=True)
    IOLoop().instance().start()


if __name__ == "__main__":

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGHUP, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    try:
        main()
    finally:
        pass
