import logging, sys
import logging.handlers

LOGNAME = b'LuoYun'
def setup(path = None, debug = 0, size = 1<<20, count = 1):
  logger = logging.getLogger(LOGNAME)
  if path == None:
    hdlr = logging.StreamHandler(sys.__stdout__)
  else:
    #hdlr = logging.FileHandler(path)
    hdlr = logging.handlers.RotatingFileHandler(path, maxBytes=size, backupCount=count)
  formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
  hdlr.setFormatter(formatter)
  logger.addHandler(hdlr) 
  if debug:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

def logger():
  return logging.getLogger(LOGNAME)

if __name__ == "__main__":
  setup(path = '/var/log/luoyun.log', count = 2)
  LOG = logger()
  LOG.info("hello")
