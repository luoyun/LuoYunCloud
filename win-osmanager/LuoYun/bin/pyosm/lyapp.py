import os, subprocess
import struct
import lydef, lylog, lyutil, lyconf

LOG = lylog.logger()
APP_Status = -1
APP_Pending = {}

def runcmd(cmdname):
  global APP_Pending
  if not APP_Pending or not APP_Pending.has_key(cmdname):
    cmd = lyconf.Config.script_dir + '\\' + cmdname
    if os.access(cmd, os.F_OK | os.X_OK):
      LOG.debug("exec: %s" % cmd)
      APP_Pending[cmdname] =  subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  if APP_Pending.has_key(cmdname):
    p = APP_Pending[cmdname]
    s = p.poll()
    if s != None:
      del APP_Pending['status']
    return (s, p)
  else:
    return (-1, None)

def run(sock = None, notify = 0):
  global APP_Status
  ret = 0
  s, p = runcmd('status')
  if s != None:
    ret = 1
    if s < 0:
      LOG.debug("status unknown")
      s = lydef.LY_S_APP_UNKNOWN
    elif s > 0:
      LOG.info("status output:")
      for o in p.stdout.readlines():
        LOG.info(o)
      s += lydef.LY_S_APP_RUNNING
    else:
      s = lydef.LY_S_APP_RUNNING
    if s != APP_Status or notify:
      LOG.info("status return code: %d" % s)
      if sock:
        d = struct.pack('i', s)
        if lyutil.socksend(sock, lydef.PKT_TYPE_OSM_REPORT, d) < 0:
          ret = -1
      APP_Status = s
  return ret
  

