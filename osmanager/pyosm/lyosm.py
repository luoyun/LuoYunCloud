#!/usr/bin/python

import getopt, sys, time, signal
import lylog, lyconf
import lyutil, lyconn, lyproc, lyapp

PROGRAM_NAME = b'lyosm.py'
PROGRAM_VERSION = b'0.4.0'
DEFAULT_OSM_CONF_PATH = b'/LuoYun/conf/luoyun.conf'
DEFAULT_OSM_LOG_PATH = b'/LuoYun/log/luoyun.log'
DEFAULT_OSM_SCRIPT_DIR = b'/LuoYun/scripts'

LOG = lylog.logger()
progrun = 1

def myexit(sig, func=None):
  global progrun
  progrun = 0
  if sig == signal.SIGTERM:
    LOG.info("TERM signal captured")
  elif sig == signal.SIGINT:
    LOG.info("INTERUPT signal captured")
  else:
    LOG.info("unknown signal captured")
  sys.exit(0)

def usage():
  print '%s OS manager of LuoYun Cloud Platform.' % PROGRAM_NAME
  print 'Usage : %s [OPTION] ' % PROGRAM_NAME
  print '  -c, --config    config file, must be full path'
  print '                  default is  %s' % DEFAULT_OSM_CONF_PATH
  print '  -l, --log       log file, must be full path'
  print '                  default is %s' %DEFAULT_OSM_LOG_PATH
  print '  -s, --script    script directory, must be full path'
  print '                  default is %s' % DEFAULT_OSM_SCRIPT_DIR
  print '  --debug         debug mode, log to strandard output'
  print '  --version       display verion'
  print '  -h, --help      '

def main():
  conf_path = DEFAULT_OSM_CONF_PATH
  log_path = DEFAULT_OSM_LOG_PATH
  script_dir = DEFAULT_OSM_SCRIPT_DIR
  debug = 0
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hc:l:s:", ["help", "version", "debug", "config=", "log=", "script="])
  except getopt.GetoptError:
    print 'Wrong command options, use -h to list command options'
    sys.exit(1)
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    if o == "--version":
      print "%s version %s" % (PROGRAM_NAME, PROGRAM_VERSION)
      sys.exit()
    if o in ("-c", "--config"):
      conf_path = a
    elif o in ("-l", "--log"):
      log_path = a
    elif o in ("-s", "--script"):
      script_dir = a
    elif o == "--debug":
      debug = 1
    else:
      print 'Wrong command options'
      sys.exit(1)
  if debug:
    lylog.setup(debug = 1)
  else:
    print "log to file %s\n" % log_path
    lylog.setup(path = log_path)
  LOG.info('Program parameters:')
  LOG.info('  config file: %s' % conf_path)
  LOG.info('  log file: %s' % log_path)
  LOG.info('  script directory: %s' % script_dir)

  lyconf.Config(conf_path)
  lyconf.Config.script_dir = script_dir
  LOG.info('Config parameters:')
  LOG.info('  tag = %d ' % lyconf.Config.tag)
  LOG.info('  clc_ip = %s ' % lyconf.Config.clc_ip)
  LOG.info('  clc_port = %d ' % lyconf.Config.clc_port)
  LOG.info('  clc_mcast_ip = %s ' % lyconf.Config.clc_mcast_ip)
  LOG.info('  clc_mcast_port = %d ' % lyconf.Config.clc_mcast_port)
  if debug:
    LOG.info('  key = %s' % lyconf.Config.key)

  signal.signal(signal.SIGTERM, myexit)
  signal.signal(signal.SIGINT, myexit)

  sock = None
  notify = 0
  appstatus = -1
  timeout = 3600
  timenow = time.time()
  while progrun:
    # connect and register osmanager with control server
    if not sock:
      sock = lyconn.connclc()
      if not sock:
        LOG.error("failed connecting clc")
        time.sleep(1)
      else:
        notify = 1
    else:
      result, response = lyutil.sockrecv(sock)
      if result == 0:
        LOG.info("close socket")
        sock.close()
        sock = None
      elif result > 0:
        lyproc.process(sock, response)
    # run scripts provided by user in script_dir
    # adjust the timeout value when neccessary
    t = time.time()
    if t - timenow >= timeout or appstatus == 0 or notify:
      timenow = t
      # lyapp.run returns 0 if any of the scripts is still running
      appstatus = lyapp.run(sock, notify)
      if appstatus > 0 and notify:
        notify = 0

  # main() function exits
  LOG.info('%s exits' % PROGRAM_NAME)
    

if __name__ == "__main__":

  main()

