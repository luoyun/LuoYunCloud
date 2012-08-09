#!/usr/bin/python

import os
import sys
import shutil
import filecmp
try:
    import json
except ImportError:
    import simplejson as json

appname = "LuoYun OS Config"
targetdir = "/LuoYun/conf"
targetpath = "%s/luoyun.conf" % (targetdir)
confsrc = "/dev/fd0"
datadir = "/root/.luoyun"
mntdir = "%s/mnt" % (datadir)
conffile = "luoyun.ini"
confpath = "%s/%s" % (mntdir, conffile)
eth0file = "ifcfg-eth0"
eth0path = "%s/%s" % (datadir, eth0file)
eth1file = "ifcfg-eth1"
eth1path = "%s/%s" % (datadir, eth1file)

def passwdconfig(passwd_hash = None):
  if not passwd_hash:
    passwd_hash = '*' 
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
  except IOError:
    print "IOError: %s" % (target)
  return

def sshkeyconfig(public_key = None):
  if not public_key:
    public_key = ""
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
    print "IOError: %s" % (target)
  return

def netconfig(netinf, mac = None, ip = None, netmask = None, gateway = None):
  try:
    src = ""
    target = ""
    f = None
    if netinf == "eth0":
      src = eth0path
      target = "/etc/sysconfig/network-scripts/ifcfg-eth0"
    elif netinf == "eth1":
      src = eth1path
      target = "/etc/sysconfig/network-scripts/ifcfg-eth1"
    else:
      print "netconfig failed"
      return;

    f = open(src, "w")
    w = [] 
    w.append('DEVICE="%s"\n' % (netinf))
    w.append('ONBOOT="yes"\n')
    if mac:
      w.append('HWADDR="%s"\n' % (mac))
    if ip:
      w.append('BOOTPROTO="static"\n')
      w.append('IPADDR=%s\n' % (ip))
      if ((not netmask) or (not gateway)):
        print "netconfig failed"
        return
      w.append('NETMASK=%s\n' %(netmask))
      w.append('GATEWAY=%s\n' % (gateway))
    else:
      w.append('BOOTPROTO="dhcp"\n')
    f.writelines(w)
    f.close()
    if not filecmp.cmp(src, target):
      f = open(target, "w")
      f.writelines(w)
      f.close()
  except IOError:
    print "IOError: %s" % (netinf)
  return

def main():
  try:
    if not os.path.exists(datadir):
      os.mkdir(datadir) 
    if not os.path.exists(mntdir):
      os.mkdir(mntdir) 
    if not os.path.exists(targetdir):
      os.mkdir(targetdir)
  except OSError:
    print "OS Error: mkdir"
    sys.exit(1)

  if not os.path.exists(confsrc):
    print "%s not exists, osconfig failed" % (confsrc)
    sys.exit(1)

  f = os.popen("mount %s %s" % (confsrc, mntdir))
  if f.close():
    print "OS Error: failed mount %s %s" % (confsrc, mntdir)
    sys.exit(1)

  if not os.path.exists(confpath):
    print "%s not exists, osconfig failed" % (confpath)
    f = os.popen("umount %s" % (mntdir))
    f.close()
    sys.exit(1)

  if not os.path.exists(targetpath) or not filecmp.cmp(confpath, targetpath):
    try:
      shutil.copyfile(confpath, targetpath)
    except OSError:
      print "OS Error: copyfile %s %s" % (confpath, targetpath)
      f = os.popen("umount %s" % (mntdir))
      f.close()
      sys.exit(1)

  f = os.popen("umount %s" % (mntdir))
  if f.close():
    print "OS Error: failed umount %s" % (mntdir)
    sys.exit(1)

  jsonstr = ""
  try:
    f = open(targetpath, "r")
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
    print "%s: no json config" % (appname)
    sys.exit(1)

  print "%s\n" % (jsonstr)
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

if __name__ == "__main__":

  main()

