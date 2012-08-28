# coding: utf-8

import sys, logging, json

import settings

# TODO: i18n is too ugly yet
import gettext
gettext.install( 'app', settings.I18N_PATH, unicode=False )

import tornado.ioloop
import tornado.web

from urls import tornado_settings as app_settings
from urls import handlers as app_handlers


import lyorm


from tornado.options import define, options
define("port", default=8888, help="given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):

        # SQLAlchemy connect
        self.db2 = lyorm.dbsession

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

    # save the global argv of program
    settings.CMD_ARGV = sys.argv
    print 'settings.CMD_ARGV = ', settings.CMD_ARGV

    try:
        main()
    finally:
        # TODO: dispose from db
        import lyorm
        lyorm.dbengine.dispose()
