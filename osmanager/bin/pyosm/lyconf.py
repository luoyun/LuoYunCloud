import sys
import lydef, lylog

LOG = lylog.logger()

class Config:
  tag = 0
  clc_ip = b''
  clc_port = 0
  clc_mcast_ip = b''
  clc_mcast_port = 0
  key = b''
  json = b''
  local_ip = b''
  status = lydef.OSM_STATUS_INIT

  def __init__(self, confpath):
    try:
      f = open(confpath)
      for l in f.readlines():
        l = l.strip()
        if not l:
          continue
        k,v = l.split('=', 1)
        if k == 'CLC_IP':
          Config.clc_ip = v
        elif k == 'CLC_PORT':
          Config.clc_port = int(v)
        elif k == 'CLC_MCAST_IP':
          Config.clc_mcast_ip = v
        elif k == 'CLC_MCAST_PORT':
          Config.clc_mcast_port = int(v)
        elif k == 'TAG':
          Config.tag = int(v)
        elif k == 'KEY':
          Config.key = v
        elif k == 'JSON':
          Config.json = v
    except IOError:
      LOG.error("Failed reading %s" % confpath)
      sys.exit(1)

if __name__ == "__main__":
  lylog.setup()
  Config('/LuoYun/conf/luoyun.conf')
  LOG.info(Config.clc_ip)
  LOG.info(Config.json)

