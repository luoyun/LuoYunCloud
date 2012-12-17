# -*- coding: utf-8 -*-
import os
import sys
import lylog

try:
    import json
except ImportError:
    import simplejson as json

LOG = lylog.logger()
def GetIp(confpath):
  try:
    f = open(confpath,"r")
    for line in f.readlines():
        line = line.rstrip()
        j = ""
        if line[:5] == 'JSON=':
            j = line[5:]
            j.strip()
        print j
        if j:
            c = json.loads(j) 
            if c.has_key("network"):
                nameserver = c["nameservers"].encode('gb2312')
                ip = c["network"][0]["ip"].encode('gb2312')
                netmask = c["network"][0]["netmask"].encode('gb2312')
                gateway = c["network"][0]["gateway"].encode('gb2312')
                u = u'本地连接'
                LocalConnection = u.encode('gb2312')
                cmd1 = "netsh interface ip set address \"%s\" static %s %s %s %i" % (LocalConnection,ip,netmask,gateway,1) 
                cmd2 = "netsh interface ip set dns %s static %s" % (LocalConnection, nameserver)
                os.system(cmd1)
                os.system(cmd2)
                LOG.info("OS Manager set %s to %s" % (LocalConnection, ip))
            else:
                u = u'本地连接'
                LocalConnection = u.encode('gb2312')
                cmd ="netsh interface ip set address %s dhcp" % LocalConnection
                os.system(cmd)
                LOG.info("OS Manager set %s to dhcp" % (LocalConnection))
  except IOError:
    LOG.error("Failed reading %s" % confpath)
    sys.exit(1)
