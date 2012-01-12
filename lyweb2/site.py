# coding: utf-8

import logging
import psycopg2

import settings

import tornado.ioloop
import tornado.web

from urls import settings as app_settings
from urls import handlers as app_handlers

import lydb


from tornado.options import define, options
define("port", default=8888, help="run on the given port", type=int)
define("dbhost", default="localhost", help="database host")
define("dbname", default="luoyun", help="database name")
define("dbuser", default="luoyun", help="database user")
define("dbpassword", default="luoyun", help="database password")


class Application(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, app_handlers, **app_settings)

        # Have one global connection to the DB across all handlers
        self.db = lydb.Connection(
            host=options.dbhost, database=options.dbname,
            user=options.dbuser, password=options.dbpassword)


application = Application()


def main():

    import sys
    reload(sys)
    sys.setdefaultencoding('utf8') 

    # Locale
    tornado.locale.load_gettext_translations(settings.I18N_PATH, "luoyun")
    #tornado.locale.set_default_locale('zh_CN')

    # options
    tornado.options.parse_command_line()

    logging.info("starting torando web server")

    # Start listen
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":

    main()
