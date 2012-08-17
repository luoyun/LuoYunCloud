#!/usr/bin/python

import os
import sys
import getopt
import shutil
import filecmp
try:
    import json
except ImportError:
    import simplejson as json

PROGRAM_NAME = "osconfig"
DEFAULT_OSM_CONF_PATH = "/LuoYun/conf/luoyun.conf"
datadir = "/root/.luoyun"

def passwdconfig(passwd_hash = None):
  if not passwd_hash:
    #passwd_hash = '*' 
    print "%s: skip configuring root password" % PROGRAM_NAME
    return
  src = "%s/shadow" % (datadir)
  target = "/etc/shadow"
  try:
    f = open(target, "r")
    w = []
    for l in f.readlines():
      e = l.split(":")
      if e[0] == "root":
        if e[1] == passwd_hash:
          return
        e[1] = passwd_hash
        w.append(":".join(e))
      elif l[0] != '\0':
        w.append(l)
    f.close()
    f = open(src, "w")
    f.writelines(w)
    f.close()
    os.rename(src, target)
  except:
    print "%s Error: %s" % (PROGRAM_NAME, target)
  return

def sshkeyconfig(public_key = None):
  if not public_key:
    #public_key = ""
    print "%s: skip configuring root ssh key" % PROGRAM_NAME 
    return
  src = "%s/authorized_keys" % (datadir)
  target = "/root/.ssh/authorized_keys"
  try:
    if not os.path.exists("/root/.ssh"):
      os.mkdir("/root/.ssh")
    f = open(src, "w")
    f.write(public_key)
    f.close()
    if os.path.exists(target) and filecmp.cmp(src, target):
      return
    os.rename(src, target)
  except IOError:
    print "%s Error: %s" % (PROGRAM_NAME, target)
  return

def netconfig(netinf, mac = None, ip = None, netmask = None, gateway = None):
  try:
    if not ip:
      # use default settting
      return

    if netinf != "eth0" and netinf != "eth1":
      print "%s only supports eth0 and eth1" % PROGRAM_NAME
      return
    
    if netmask == None or (netinf == "eth1" and gateway == None):
      print "%s Error: missing config info for  %s" % (PROGRAM_NAME, netinf)
      return

    f = os.popen("/sbin/ifconfig %s 2>&1" % netinf)
    for l in f.readlines():
      True
    if f.close() == None:
      f = os.popen("/sbin/ifdown %s 2>&1" % netinf)
      l = "".join([ l for l in f.readlines() ])
      if f.close():
        print "%s Error: failed bringing down %s" % (PROGRAM_NAME, netinf)
        if l:
          print l
        return

    f = os.popen("/sbin/ifconfig %s %s netmask %s 2>&1" % (netinf, ip, netmask))
    l = "".join([ l for l in f.readlines() ])
    if f.close():
      print "%s Error: failed bringing up %s" % (PROGRAM_NAME, netinf)
      if l:
        print l
      return

    if netinf == "eth0":
      f = os.popen("/sbin/route add -net default gw %s eth0 2>&1" % gateway)
      l = "".join([ l for l in f.readlines() ])
      # ignore error if route exists
      if f.close() and l[:22] != 'SIOCADDRT: File exists':
        print "%s Error: failed adding default route %d" % (PROGRAM_NAME, r)
        if l:
          print l

  except:
    print "%s Error: %s" % (PROGRAM_NAME, netinf)

def nameserverconfig(nameserver = None):
  if not nameserver:
    return
  src = "%s/resolv.conf" % (datadir)
  target = "/etc/resolv.conf"
  try:
    f = open(src, "w")
    for l in nameserver.split():
      f.write("nameserver %s\n" % l)
    f.close()
    if os.path.exists(target) and filecmp.cmp(src, target):
      return
    os.rename(src, target)
  except IOError:
    print "%s Error: %s" % (PROGRAM_NAME, target)
  return

def main():
  if not os.path.exists(confpath):
    print "%s: config file %s not exist" % (PROGRAM_NAME, confpath)
    sys.exit(1)

  try:
    if not os.path.exists(datadir):
      os.mkdir(datadir) 
  except OSError:
    print "OS Error: mkdir"
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

  if not jsonstr:
    print "%s: no json config" % (PROGRAM_NAME)
    sys.exit(1)

  # print "%s\n" % (jsonstr)
  j = json.loads(jsonstr)
  if j.get("network"):
    n = len(j["network"])    
    netconfig("eth0",
              j["network"][0].get("mac"),
              j["network"][0].get("ip"),
              j["network"][0].get("netmask"),
              j["network"][0].get("gateway"))
    if n > 1:
      netconfig("eth1",
                j["network"][1].get("mac"),
                j["network"][1].get("ip"),
                j["network"][1].get("netmask"),
                j["network"][1].get("gateway"))
  if j.get("public_key"):
    sshkeyconfig(j["public_key"])
  else:
    sshkeyconfig()
  if j.get("passwd_hash"):
    passwdconfig(j["passwd_hash"])
  else:
    passwdconfig()
  if j.get("nameserver"):
    nameserverconfig(j["nameserver"])

def usage():
  print '%s Configure essential system settings' % PROGRAM_NAME
  print 'Usage : %s [OPTION] ' % PROGRAM_NAME
  print '  -c, --config    config file, must be full path'
  print '                  default is  %s' % DEFAULT_OSM_CONF_PATH
  print '  -h, --help      '

if __name__ == '__main__':
  confpath = DEFAULT_OSM_CONF_PATH
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hc:l:", ["help", "config=", "log="])
  except getopt.GetoptError:
    print 'Wrong command options, use -h to list command options'
    sys.exit(1)
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    if o in ("-c", "--config"):
      confpath = a
    else:
      print 'Wrong command options'
      sys.exit(1)

  main()

