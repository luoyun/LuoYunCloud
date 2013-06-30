import httplib
import logging
import json
import time

from lyc.handler import TCPStreamHandler, MSGStream
#from lyc.client import LYTCPClient


class WebConnection(TCPStreamHandler):

#    def __init__(self, application=None, sock=None, ioloop=None, client_address=None, server_address=None):
    def __init__(self, application, ioloop, host=None, port=None, **kwargs):

        self.host = host if host else '127.0.0.1'
        self.port = port if port else 8888
        self._callbacks = {} # ID -> callback_func
        super(WebConnection, self).__init__(application=application, ioloop=ioloop)


    def data_received(self, data):
        logging.debug('received data: %s', data)

        call = data.get('call', None)

        if call:
            return # self._run_callback(data)

        key = data.get('key', None)

        if not key:
            logging.error('No key !')
            return

        for k, v in request_mapping:
            print 'k = ', k
            if k == key:
                print 'k == key'
                handler = v(connection=self, request=data)
                handler._execute()
                return True

        return False

    def _run_callback(self, data):
        call = data.get('call', None)

        if not call:
            logging.error('Msg can not have call id !')
            return False

        if call not in self._callbacks:
            logging.error('No call id found in locale connection !')
            return False

        return self._callbacks[call](data)

    def add_callback(self, call_id, callback):
        if call_id in self._callbacks:
            logging.error('Call id exists: %s', call_id)
            return False

        self._callbacks[call_id] = callback

    def after_close(self):
        time.sleep(1)
        logging.info('reconnect to %s:%s', self.host, self.port)
        self.conn.close()
        self.sock = None
        self.connect()

    def connect(self):

        data = {"type": 'lyclc', "password": 'SziniXEagen4+49G40zEGQ'}
        params = json.dumps(data)

        try:
            
            self.conn = httplib.HTTPConnection("%s:%s" % (self.host, self.port))
            self.conn.request('POST', '/api/clc/register', params)
        
            #data = conn.getresponse().read()
            #print 'data = ', data

            self.sock = self.conn.sock
#            self.stream = MSGStream(self.sock)
            self.ioloop.add_handler(self.sock.fileno(), self, self.ioloop.READ)
            logging.debug('connect to %s:%s success.', self.host, self.port)

        except Exception, e:
            logging.error('connect to %s:%s faile: %s', self.host, self.port, e )
            deadline = time.time() + 3 # after 1 second
            self.ioloop.add_timeout(deadline, self.connect)


class RequestHandler(object):

    def __init__(self, connection, request, **kwargs):
        self.connection = connection
        self.request = request

    def _execute(self):
        self.get()

    def get(self):
        raise NotImplementedError


class InstanceControl(RequestHandler):

    def get(self):
        print 'request: %s' % self.request
        print 'self.connection.application.nodes = ', self.connection.application.nodes
        call_id = self.connection.application.get_unique_id()
        self.connection.add_callback(call_id, self.call_back)
        self.connection.stream.send_msg(msg={'call': call_id, 'test': 'callback test'}, key='lyweb.instance.status.update')

    def callback(self, data):
        logging.debug('I am callback, data: ', data)


class WebRegister(RequestHandler):

    def get(self):
        print 'request: %s' % self.request
        self.connection.application.register_web_connection(self)


request_mapping = [
    ('lyclc.instance.control', InstanceControl),
    ]
    
