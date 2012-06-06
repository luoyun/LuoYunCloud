import sys
import lydef, lylog

LOG = lylog.logger()

class Config:
  tag = 0
  clc_ip = b''
  clc_port = 0
  clc_mcast_ip = b''
  clc_mcast_port = 0
  storage_ip = b''
  storage_method = 0
  storage_parm = b''
  key = b''
  local_ip = b''
  status = lydef.OSM_STATUS_INIT

  def __init__(self, confpath, keypath):
    try:
      f = open(confpath)
      for l in f.readlines():
        l = l.rstrip()
        k,v = l.split('=')
        if k == 'CLC_IP':
          Config.clc_ip = v
        elif k == 'CLC_PORT':
          Config.clc_port = int(v)
        elif k == 'CLC_MCAST_IP':
          Config.clc_mcast_ip = v
        elif k == 'CLC_MCAST_PORT':
          Config.clc_mcast_port = int(v)
        elif k == 'STORAGE_IP':
          Config.storage_ip = v
        elif k == 'STORAGE_METHOD':
          Config.storage_method = int(v)
        elif k == 'STORAGE_PARM':
          Config.storage_parm = v
        elif k == 'TAG':
          Config.tag = int(v)
    except IOError:
      LOG.error("Failed reading %s" % confpath)
      sys.exit(1)
    try:
      f = open(keypath)
      Config.key = f.readline()
    except IOError:
      LOG.error("Failed reading %s" % keypath)
      sys.exit(1)

if __name__ == "__main__":
  lylog.setup()
  Config('/LuoYun/conf/luoyun.conf', '/LuoYun/conf/luoyun.key')
  LOG.info(Config.clc_ip)
  LOG.info(Config.key)
