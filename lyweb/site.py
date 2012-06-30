# coding: utf-8

import logging

import settings

# TODO: i18n is too ugly yet
import gettext
gettext.install( 'app', settings.I18N_PATH, unicode=False )

import tornado.ioloop
import tornado.web

from urls import settings as app_settings
from urls import handlers as app_handlers

import lyorm


from tornado.options import define, options
define("port", default=8888, help="given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, app_handlers, **app_settings)

        # SQLAlchemy connect
        self.db2 = lyorm.dbsession



def main():
    import sys,signal
    reload(sys)
    sys.setdefaultencoding('utf8') 

    def signal_handler(signal, frame):
        print "...You Pressed CTL+C ,exit..."
        sys.exit(1)
        # end def

    # Locale
    tornado.locale.load_gettext_translations(settings.I18N_PATH, "luoyun")
    #tornado.locale.set_default_locale('zh_CN')

    # options
    tornado.options.parse_command_line()

    logging.info("starting torando web server")

    # Start listen
    application = Application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

    # wait for singal
    signal.pause()



if __name__ == "__main__":

    try:
        main()
    finally:
        # TODO: dispose from db
        import lyorm
        lyorm.dbengine.dispose()
