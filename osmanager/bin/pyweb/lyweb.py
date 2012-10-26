#!/usr/bin/python

import sys
import os
import getopt
from string import Template
import Cookie
import urlparse
import posixpath
import urllib
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

try:
    import json
except ImportError:
    import simplejson as json

import luoyuninfo
import lylog

PROGRAM_NAME = b'LYWEB'
DEFAULT_OSM_CONF_PATH = b'/LuoYun/conf/luoyun.conf'
DEFAULT_WEB_LOG_PATH = b'/LuoYun/log/lyweb.log'
DEFAULT_WEB_PAGE_DIR = b'/LuoYun/custom/www'
DEFAULT_WEB_PORT = 8080
luoyun_cookie = b''
luoyun_domain = None
LOG = lylog.logger()

class LuoYunHttpRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Serve a GET request."""
        # if "Cookie" in self.headers:
        #    c = Cookie.SimpleCookie(self.headers["Cookie"])
        #    print c
        f = self.send_head()
        if f:
            s = Template(f.read())
            d = luoyuninfo.get_sysinfo(luoyun_domain)
            # print d
            self.wfile.write(s.safe_substitute(d))
            f.close()

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        depending on the query string given on the URL, the path is
        prefix-ed with /withcookie and /nocookie
        """

        # check cookie
        u = urlparse.urlparse(path)
        e = urlparse.parse_qs(u[4])
        if luoyun_cookie and e and e.has_key('cookie') and e['cookie'][0] == luoyun_cookie:
            path = "/withcookie%s" % u[2]
        else:
            path = "/nocookie%s" % u[2]
        print path

        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path


def main(HandlerClass = LuoYunHttpRequestHandler,
         ServerClass = BaseHTTPServer.HTTPServer, port = 8080):
    server_address = ('', port)
    httpd = ServerClass(server_address, HandlerClass)
    httpd.serve_forever()


def usage():
  print '%s Start simple http server used by LuoYun Cloud Platform.' % PROGRAM_NAME
  print 'Usage : %s [OPTION] ' % PROGRAM_NAME
  print '  -c, --config    config file, must be full path'
  print '                  default is  %s' % DEFAULT_OSM_CONF_PATH
  print '  -l, --log       log file, must be full path'
  print '                  default is %s' % DEFAULT_WEB_LOG_PATH
  print '  -w, --web       web file directory, must be full path'
  print '                  default is %s' % DEFAULT_WEB_PAGE_DIR
  print '  -p, --port      http server listening'
  print '                  default is %s' % DEFAULT_WEB_PORT
  print '  -h, --help      '

if __name__ == '__main__':
    confpath = DEFAULT_OSM_CONF_PATH
    logpath = DEFAULT_WEB_LOG_PATH
    webdir = DEFAULT_WEB_PAGE_DIR
    webport = DEFAULT_WEB_PORT
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:l:p:w:",
                              ["help", "config=", "log=", "port=", "web="])
    except getopt.GetoptError:
        print 'Wrong command options, use -h to list command options'
        sys.exit(1)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-c", "--config"):
            confpath = a
        elif o in ("-l", "--log"):
            logpath = a
        elif o in ("-p", "--port"):
            webport = int(a)
        elif o in ("-w", "--web"):
            webdir = a
        else:
            print 'Wrong command options'
            sys.exit(1)

    lylog.setup(logpath)

    jsonstr = ""
    try:
        f = open(confpath, "r")
        for l in f.readlines():
            if l[:5] == 'JSON=':
                jsonstr = l[5:]
                jsonstr.strip()
                break
        f.close()
    except IOError:
        print "IOError: processing %s" % (confpath)
        sys.exit(1)

    if jsonstr:
        j = json.loads(jsonstr)
        if j and j.has_key("cookie"):
            luoyun_cookie = j["cookie"]
        if j and j.has_key("domain") and j["domain"].has_key("name"):
            luoyun_domain = j["domain"]["name"]

    p = os.path.dirname(sys.argv[0])
    sys.path.append(p)
    os.chdir(webdir)
    main(port=webport)

