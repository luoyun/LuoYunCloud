import struct
import logging
import cStringIO
import json
import time
from ioloop import IOLoop


class MSGFormat(object):

    def __init__(self, head, body):
        self.type = head.get('type', 0)
        self.length = head.get('length', 0)
        # TODO: other data type
        self.body = self._load_json(body)

    def _load_json(self, data):
        if not data:
            return None
        try:
            return json.loads(data)
        except Exception, e:
            logging.error('load json data failed: %s', e)
            return None



class MSGStream(object):
    ''' read a msg from sock '''

    headlen = 1 + 1 + 2 + 4    # SOH + 1B + type + length
    bodymax = 10 * 1024 * 1024 # 10Mb

    # common msg type
    request_msg  = 1
    response_msg = 2

    def __init__(self, sock):
        self.sock = sock

    def _read_from_stream(self, length):

        if not self.sock:
            return

        iostream = cStringIO.StringIO()
        left = length

        try:
            while True:
                buffer_len = 2048 if left > 2048 else left
                data = self.sock.recv(buffer_len)
                datalen = len(data)
                if datalen == 0:
                    return

                left = left - datalen
                iostream.write(data)

                if left == 0:
                    break
                if left < 0:
                    return

        except Exception, e:
            logging.error('read from stream: %s', e)
            return

        return iostream.getvalue()


    def read_msg(self):

        head = {}

        # read data
        data = self._read_from_stream(self.headlen)
        #logging.debug('read head: %s', data)
        if not data:
            return

        start, x, head['type'], head['length'] = struct.unpack('bbhi', data)
        if start != 01:
            logging.error('wrong header start value: %s', start)
            return

        if head['length'] > self.bodymax:
            logging.error('msg length (%s) is too large!', msglen)
            return

        # read body
        if head['length'] > 0:
            body = self._read_from_stream(head['length'])
            #logging.debug('read body: %s', body)
            if not body:
                logging.error('read msg body failed.')
                return

        msg = MSGFormat(head, body)
        # TODO: for debug
        #msg.body['received_time'] = time.time()

        # TODO: for debug
        logging.debug('msg received: %s', msg.body)

        return msg


    def send_msg(self, msg, key=None, call=None, call_me=None):

        if not key:
            return False
        
        body = { #'send_time': time.time(), # TODO: for debug
                 'msg': msg }

        if key:
            body['key'] = key
        if call:
            body['call'] = call
        if call_me:
            body['call_me'] = call_me

        body = json.dumps(body)
        bodylen = len(body)
        head = struct.pack('bbhi', 01, 02, 03, bodylen)
        msglen = self.headlen + bodylen

        try:
            # TODO: USE JSON
            sendlen = self.sock.send(head + body)
            if sendlen != msglen:
                logging.error('send msg failed: sendlen(%s) != msglen(%s+%s)',
                              sendlen, self.headlen, bodylen)
        except Exception, e:
            logging.error('send msg failed: %s', e)
            return False

        return True



class TCPStreamHandler(object):
    ''' Basic handler for socket events '''

    def __init__(self, application=None, sock=None, ioloop=None, client_address=None, server_address=None):
        self.application = application
        self.sock = sock
        self.ioloop = ioloop
        self.client_address = client_address
        self._stream = None

    @property
    def sockfd(self):
        return self.sock.fileno() if self.sock else None

    @property
    def stream(self):
        if not self._stream and self.sock:
            self._stream = MSGStream(self.sock)
        return self._stream

    def _handle_read(self):
        data = self.stream.read_msg()
        if data:
            self.data_received(data.body)
        else:
            self._handle_close()

    def _handle_write(self):
        pass

    def _handle_close(self):

        logging.debug('close sock(%s).', self.sockfd)

        if self.sock and self.sockfd:
            self.ioloop.remove_handler(self.sockfd)

        self.sock.close()
        self.sock = None
        self.after_close()

    def data_received(self, data):
        raise NotImplementedError()

    def after_close(self):
        pass

    def __call__(self, fd, events):

        if not self.sock:
            logging.error("Got events for closed stream %d", fd)
            return

        if events & IOLoop.READ:
#            logging.debug('IOLoop.READ event happen on %s.', self.__class__.__name__)
            self._handle_read()

        elif events & IOLoop.WRITE:
            logging.debug('IOLoop.WRITE event happen on %s.', self.__class__.__name__)
            self._handle_write()

        else:
            logging.debug('other event happen. close handler')
            self._handle_close()
