import logging
import ssl

from lyc.netutil import bind_sockets, add_accept_handler

from handler.base import NewClientHandler


class Application(object):

    _cur_unique_id = 0

    def __init__(self, ioloop, ssl_options=None):

        self.ioloop = ioloop
        self.ssl_options = ssl_options

        self.nodes   = []  # all nodes
        self.sockets = {}  # all sockets: fd -> socket

        self._web = ()      # web connection info


    def listen(self, port, address = '0.0.0.0'):

        socks = bind_sockets(port, address)

        for s in socks:
            add_accept_handler(s, self.handle_stream, self.ioloop)

        logging.info('starting listen on port %s', port)


    def handle_stream(self, stream, address):

        logging.debug('new client (%s) on fd(%s)', address, stream.fileno())

        if self.ssl_options is not None:
            assert ssl, "Python 2.6+ and OpenSSL required for SSL"
            try:
                stream = ssl.wrap_socket(stream,
                                         server_side=True,
                                         do_handshake_on_connect=False, # TODO: this ?
                                         **self.ssl_options)
                stream.do_handshake() # TODO: import for multi non-blocking
            except ssl.SSLError, err:
                if err.args[0] == ssl.SSL_ERROR_EOF:
                    return stream.close()
                else:
                    raise
            except socket.error, err:
                if err.args[0] == errno.ECONNABORTED:
                    return stream.close()
                else:
                    raise

        h = NewClientHandler(self, stream, self.ioloop, client_address=address)
        self.ioloop.add_handler(stream.fileno(), h, self.ioloop.READ)

    def get_unique_id(self):
        self._cur_unique_id += 1
        return self._cur_unique_id

    def register_node_connection(self, handler):
        pass
    def remove_node_connection(self, handler):
        pass
    def register_web_connection(self, handler, data):
        logging.debug('data = ' , data)
    def remove_web_connection(self, handler):
        pass
