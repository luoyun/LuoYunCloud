import logging
import random
from lyc.netutil import bind_sockets, add_accept_handler
from lyc.ioloop import IOLoop
from lyc.handler import TCPStreamHandler

import ssl
from lyc.security import get_enc_password, check_password


class NodeStreamHandler(TCPStreamHandler):

    def data_received(self, data):
        logging.debug('node data: %s', data)

        call = data.body.get('call', None)

        if call:
            return # self._run_callback(data)

        key = data.body.get('key', None)

        if not key:
            logging.error('No key !')
            return
        
        self.stream.send_msg(msg='test', key='test.lyclc')

    def close_connection(self):
        logging.debug('close node connection: %s on fd(%s)',
                      self.client_address, self.sock.fileno())



