#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import signal
import logging
import select
from optparse import OptionParser

# Global PATH
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../../lib/'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../../'))
sys.path.insert(0, '/opt/LuoYun/web/')


# TODO: i18n is too ugly yet
import __builtin__
__builtin__.__dict__['_'] = lambda s: s

from lyc.log import initlog
from lyc.ioloop import IOLoop

from clcapp import Application



def parse_option():

    import multiprocessing
    cpu_core_num = multiprocessing.cpu_count()

    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-L", "--logfile", dest="logfile",
                      help="log into FILE", metavar="FILE")
    parser.add_option("-w", "--worker", dest="worker", default=cpu_core_num,
                      help="numbers of worker", metavar="int")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")

    (options, args) = parser.parse_args()
    return options, args


def exit_handler(_signal, frame):

    if _signal == signal.SIGINT:
        print " ... You Pressed CTL+C, exit ... "

    elif _signal == signal.SIGHUP:
        print " ... get SIGHUP, exit ... "

    if _signal == signal.SIGTERM:
        print " ... get SIGTERM, exit ... "


#    db.dispose()

    # TODO: quit email
    try:
        from yweb.mail import FileSysMail
        fm = FileSysMail.get_instance()
        fm.end()
    except RuntimeError:
        pass

    sys.exit(1)


def main():

    # parse option
    options, args = parse_option()

    # init log
    _logfile = options.logfile if hasattr(options, 'logfile') else None
    initlog(logfile = _logfile)

    ssl_options={
        "certfile": os.path.join(PROJECT_ROOT, 'cert.pem'),
        "keyfile": os.path.join(PROJECT_ROOT, 'cert.pem'),
        }

    ioloop = IOLoop()
    app = Application(ioloop=ioloop, ssl_options = ssl_options)

    # Connect to web
#    from handler.web import WebConnection
#    webclient = WebConnection(application=app, ioloop=ioloop, host='127.0.0.1', port=8888)
#    webclient.connect()

    app.listen(1368)

    from handler.base import start_filesysmail
    start_filesysmail()

    ioloop.start()


if __name__ == '__main__':

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGHUP, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    main()

