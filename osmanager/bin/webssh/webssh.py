#!/usr/bin/python

import sys
import os
import getopt

try:
    import json
except ImportError:
    import simplejson as json

DEFAULT_OSM_CONF_PATH = b'/LuoYun/conf/luoyun.conf'
DEFAULT_WEB_SSH_EXE = b'shellinaboxd'
DEFAULT_WEB_SSH_PORT = 8001

def usage():
  print '%s LuoYun Cloud Instance Web ssh client.' % PROGRAM_NAME
  print 'Usage : %s [OPTION] ' % PROGRAM_NAME
  print '  -c, --config    config file, must be full path'
  print '                  default is  %s' % DEFAULT_OSM_CONF_PATH
  print '  -p, --port      web ssh port'
  print '                  default is  %s' % DEFAULT_WEB_SSH_PORT
  print '  -h, --help      '

if __name__ == '__main__':
    confpath = DEFAULT_OSM_CONF_PATH
    sshport = DEFAULT_WEB_SSH_PORT
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hc:p:",
                                   ["help", "config=", "port="])
    except getopt.GetoptError:
        print 'Wrong command options, use -h to list command options'
        sys.exit(1)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-c", "--config"):
            confpath = a
        elif o in ("-p", "--port"):
            sshport = int(a)
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
        if j and j.get("webssh"):
            if j["webssh"].get("status") and j["webssh"]["status"] == "disable":
                print "web ssh disabled"
                sys.exit(0)
            if j["webssh"].get("port"):
               sshport = j["webssh"]["port"]

    p = os.path.dirname(sys.argv[0])
    f = os.popen("%s/%s -t -b -p %d -s /:SSH" % (p, DEFAULT_WEB_SSH_EXE, sshport))
    if f.close():
        print "Error: start web ssh failed"
        sys.exit(1)

