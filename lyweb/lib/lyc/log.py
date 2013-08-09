import logging


def initlog2(logfile=None, stream=None, loglevel=None):

    from logging import addLevelName
    addLevelName(logging.CRITICAL, 'C')
    addLevelName(logging.ERROR, 'E')
    addLevelName(logging.WARNING, 'W')
    addLevelName(logging.INFO, 'I')
    addLevelName(logging.DEBUG, 'D')

    if logfile:
        hdlr = logging.FileHandler(logfile)
    else:
        hdlr = logging.StreamHandler(stream)

    fmt = logging.Formatter('%(levelname)s %(asctime)s %(module)s:%(lineno)d %(message)s', datefmt='%m-%d %I:%M:%S')
    hdlr.setFormatter(fmt)

    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.DEBUG)

    if loglevel:
        logging.root.setLevel(loglevel)

    #logging.debug('init log done')


# from tornado style
def initlog(logfile=None, stream=None, loglevel='DEBUG'):
    # Set up log level and pretty console logging by default
    logging.getLogger().setLevel(getattr(logging, loglevel.upper()))
    enable_pretty_logging()


import sys
import time
try:
    import curses
except ImportError:
    curses = None

def enable_pretty_logging():
    """Turns on formatted logging output as configured.
    
    This is called automatically by `parse_command_line`.
    """
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        # Set up color if we are in a tty and curses is installed
        color = False
        if curses and sys.stderr.isatty():
            try:
                curses.setupterm()
                if curses.tigetnum("colors") > 0:
                    color = True
            except Exception:
                pass
        channel = logging.StreamHandler()
        channel.setFormatter(_LogFormatter(color=color))
        root_logger.addHandler(channel)



class _LogFormatter(logging.Formatter):
    def __init__(self, color, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self._color = color
        if color:
            # The curses module has some str/bytes confusion in python3.
            # Most methods return bytes, but only accept strings.
            # The explict calls to unicode() below are harmless in python2,
            # but will do the right conversion in python3.
            fg_color = unicode(curses.tigetstr("setaf") or 
                               curses.tigetstr("setf") or "", "ascii")
            self._colors = {
                logging.DEBUG: unicode(curses.tparm(fg_color, 4), # Blue
                                       "ascii"),
                logging.INFO: unicode(curses.tparm(fg_color, 2), # Green
                                      "ascii"),
                logging.WARNING: unicode(curses.tparm(fg_color, 3), # Yellow
                                         "ascii"),
                logging.ERROR: unicode(curses.tparm(fg_color, 1), # Red
                                       "ascii"),
            }
            self._normal = unicode(curses.tigetstr("sgr0"), "ascii")

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception, e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        record.asctime = time.strftime(
            "%y%m%d %H:%M:%S", self.converter(record.created))
        prefix = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]' % \
            record.__dict__
        if self._color:
            prefix = (self._colors.get(record.levelno, self._normal) +
                      prefix + self._normal)
        formatted = prefix + " " + record.message
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted = formatted.rstrip() + "\n" + record.exc_text
        return formatted.replace("\n", "\n    ")
