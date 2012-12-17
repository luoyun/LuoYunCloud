import logging, sys
import logging.handlers

LOGNAME = b'LuoYun'

class StreamToLogger(object):
   """
   Fake file-like stream object that redirects writes to a logger instance.
   """
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''
 
   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())
 
def setup(path = None, debug = 0, size = 1<<20, count = 1):
  if path == None:
    hdlr = logging.StreamHandler(sys.__stdout__)
    filename = None
  else:
    hdlr = logging.handlers.RotatingFileHandler(path, maxBytes=size, backupCount=count)
    filename = path
  if debug:
    level = logging.DEBUG
  else:
    level = logging.INFO
  logging.basicConfig(
     handlers=hdlr,
     level=level,
     format='%(asctime)s [%(levelname)s] %(message)s',
     filename=path,
     filemode='a',
  )

  stdout_logger = logging.getLogger('STDOUT')
  sl = StreamToLogger(stdout_logger, logging.INFO)
  sys.stdout = sl
 
  stderr_logger = logging.getLogger('STDERR')
  sl = StreamToLogger(stderr_logger, logging.INFO)
  sys.stderr = sl
  return

def logger():
  return logging.getLogger(LOGNAME)

if __name__ == "__main__":
  setup(path = '/var/log/luoyun.log', debug = 1, size = 100, count = 2)
  #setup(path = None, count = 2)
  LOG = logger()
  LOG.info("hello")
  print "Test to standard out"
  raise Exception('Test to standard error')
