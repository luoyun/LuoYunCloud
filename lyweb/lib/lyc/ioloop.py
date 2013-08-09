import logging
import select
import time
import errno
import heapq
import datetime

class IOLoop(object):

    READ = select.EPOLLIN
    WRITE = select.EPOLLOUT
    ERROR = select.EPOLLERR | select.EPOLLHUP

    def __init__(self):
        self._impl = select.epoll()
        self._handlers = {} # fd -> handler
        self._timeouts = []
#        self._callbacks = {} # id -> callback

    def start(self):

        while True:
            poll_timeout = 3600.0

            if self._timeouts:
                now = time.time()
                while self._timeouts:
                    if self._timeouts[0].callback is None:
                        # the timeout was cancelled
                        heapq.heappop(self._timeouts)
                    elif self._timeouts[0].deadline <= now:
                        timeout = heapq.heappop(self._timeouts)
                        self._run_callback(timeout.callback)
                    else:
                        seconds = self._timeouts[0].deadline - now
                        poll_timeout = min(seconds, poll_timeout)
                        break

            events = self._impl.poll(poll_timeout)
            #logging.debug('events: %s', events)

            for fd, evt in events:
                try:
                    self._handlers[fd](fd, evt)
                except (OSError, IOError), e:
                    if e.args[0] == errno.EPIPE:
                        # Happens when the client closes the connection
                        pass
                    else:
                        logging.error("Exception in I/O handler for fd %s",
                                      fd, exc_info=True)
#                        self.remove_handler(fd)
                except Exception:
                    logging.error("Exception in I/O handler for fd %s",
                                  fd, exc_info=True)
#                    self.remove_handler(fd)
#                    try:
#                        self._handlers[fd].close_connection()
#                        self._handlers[fd].after_close()
#                    except Exception, e:
#                        logging.error('exec close failed: %s', e)



    def add_handler(self, fd, handler, evt):

        if fd in self._handlers:
            logging.error('handler for fd(%s), evt(%s) exist.' % (fd, evt))
            self.remove_handler(fd)
#            return

        self._handlers[fd] = handler
#        logging.debug("binding handler(%s) on fd(%s)" % (handler.__class__.__name__, fd))
        #self._impl.register(fd, evt | select.EPOLLERR | select.EPOLLHUP)
        self._impl.register(fd, evt | self.ERROR)

    def update_handler(self, fd, evt):
        """Changes the events we listen for fd."""
        self._impl.modify(fd, evt)

    def remove_handler(self, fd):

        if fd in self._handlers:
            module_name = self._handlers[fd].__class__.__name__
        else:
            module_name = 'unknown handler'
        self._handlers.pop(fd, None)
#        logging.debug("unbinding handler(%s) on fd(%s)" % (module_name, fd))
        try:
            self._impl.unregister(fd)
        except (OSError, IOError):
            logging.debug("Error deleting fd from IOLoop", exc_info=True)


    def _run_callback(self, callback):
        try:
            callback()
        except Exception, e:
            logging.error('run callback %s failed: %s', callback, e)


    def add_timeout(self, deadline, callback):
        """Calls the given callback at the time deadline from the I/O loop.

        Returns a handle that may be passed to remove_timeout to cancel.

        ``deadline`` may be a number denoting a unix timestamp (as returned
        by ``time.time()`` or a ``datetime.timedelta`` object for a deadline
        relative to the current time.

        Note that it is not safe to call `add_timeout` from other threads.
        Instead, you must use `add_callback` to transfer control to the
        IOLoop's thread, and then call `add_timeout` from there.
        """
#        logging.debug('add_timeout, %s, %s', deadline, callback)
        timeout = _Timeout(deadline, callback)
        heapq.heappush(self._timeouts, timeout)
        return timeout

    def remove_timeout(self, timeout):
        """Cancels a pending timeout.

        The argument is a handle as returned by add_timeout.
        """
        # Removing from a heap is complicated, so just leave the defunct
        # timeout object in the queue (see discussion in
        # http://docs.python.org/library/heapq.html).
        # If this turns out to be a problem, we could add a garbage
        # collection pass whenever there are too many dead timeouts.
        timeout.callback = None



class _Timeout(object):
    """An IOLoop timeout, a UNIX timestamp and a callback"""

    # Reduce memory overhead when there are lots of pending callbacks
    __slots__ = ['deadline', 'callback']

    def __init__(self, deadline, callback):
        if isinstance(deadline, (int, long, float)):
            self.deadline = deadline
        elif isinstance(deadline, datetime.timedelta):
            self.deadline = time.time() + _Timeout.timedelta_to_seconds(deadline)
        else:
            raise TypeError("Unsupported deadline %r" % deadline)
        self.callback = callback

    @staticmethod
    def timedelta_to_seconds(td):
        """Equivalent to td.total_seconds() (introduced in python 2.7)."""
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / float(10**6)

    # Comparison methods to sort by deadline, with object id as a tiebreaker
    # to guarantee a consistent ordering.  The heapq module uses __le__
    # in python2.5, and __lt__ in 2.6+ (sort() and most other comparisons
    # use __lt__).
    def __lt__(self, other):
        return ((self.deadline, id(self)) <
                (other.deadline, id(other)))

    def __le__(self, other):
        return ((self.deadline, id(self)) <=
                (other.deadline, id(other)))


class PeriodicCallback(object):
    """Schedules the given callback to be called periodically.

    The callback is called every callback_time milliseconds.

    `start` must be called after the PeriodicCallback is created.
    """
    def __init__(self, callback, callback_time, io_loop=None):
        self.callback = callback
        self.callback_time = callback_time
        self.io_loop = io_loop or IOLoop.instance()
        self._running = False
        self._timeout = None

    def start(self):
        """Starts the timer."""
        self._running = True
        self._next_timeout = time.time()
        self._schedule_next()

    def stop(self):
        """Stops the timer."""
        self._running = False
        if self._timeout is not None:
            self.io_loop.remove_timeout(self._timeout)
            self._timeout = None

    def _run(self):
        if not self._running: return
        try:
            self.callback()
        except Exception:
            logging.error("Error in periodic callback", exc_info=True)
        self._schedule_next()

    def _schedule_next(self):
        if self._running:
            current_time = time.time()
            while self._next_timeout <= current_time:
                self._next_timeout += self.callback_time / 1000.0
            self._timeout = self.io_loop.add_timeout(self._next_timeout, self._run)



