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

DEFAULT_OSM_CONF_PATH = b'/LuoYun/conf/luoyun.conf'
luoyun_cookie = b''
luoyun_domain = None

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
         ServerClass = BaseHTTPServer.HTTPServer):
    BaseHTTPServer.test(HandlerClass, ServerClass)

def usage():
  print '%s OS manager of LuoYun Cloud Platform.' % PROGRAM_NAME
  print 'Usage : %s [OPTION] ' % PROGRAM_NAME
  print '  -c, --config    config file, must be full path'
  print '                  default is  %s' % DEFAULT_OSM_CONF_PATH
  print '  -h, --help      '

if __name__ == '__main__':
    confpath = DEFAULT_OSM_CONF_PATH
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "config="])
    except getopt.GetoptError:
        print 'Wrong command options, use -h to list command options'
        sys.exit(1)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-c", "--config"):
            conf_path = a
        else:
            print 'Wrong command options'
            sys.exit(1)

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
    os.chdir("%s/data" % p)
    main()
