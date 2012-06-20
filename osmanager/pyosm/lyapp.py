import os, subprocess
import struct
import lydef, lylog, lyutil, lyconf

LOG = lylog.logger()
APP_Status = -1
APP_Pending = {}

def run(sock):
  global APP_Pending, APP_Status
  # run application status, if it exists
  if not APP_Pending:
    cmd = lyconf.Config.script_dir + '/status'
    if os.access(cmd, os.F_OK | os.X_OK):
       LOG.debug("exec: %s" % cmd)
       APP_Pending['status'] =  subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  s = lydef.LY_S_APP_UNKNOWN
  if APP_Pending.has_key('status'):
    p = APP_Pending['status']
    s = p.poll()
    if s == None:
      return
    del APP_Pending['status']
    LOG.debug("status output:")
    for o in p.stdout.readlines():
      LOG.debug(o)
    if s < 0:
      return
    s += lydef.LY_S_APP_RUNNING;

  if s != APP_Status:
    LOG.info("status return code: %d" % s)
    d = struct.pack('i', s)
    lyutil.socksend(sock, lydef.PKT_TYPE_OSM_REPORT, d)
    APP_Status = s 
