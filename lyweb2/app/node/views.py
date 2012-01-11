# coding: utf-8

import logging, datetime, time
import tornado
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous


class Index(LyRequestHandler):

    def get(self):

        nodes = self.db.query('SELECT * from node;')

        d = { 'title': 'Servers Home', 'nodes': nodes }

        self.render('node/index.html', **d)


class DynamicList(LyRequestHandler):

    @asynchronous
    def get(self):

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.have_new_node(now)


    def have_new_node(self, now):

        if self.request.connection.stream.closed():
            return

        nodes = self.db.query(
            'SELECT * from node WHERE updated > %s;',
            now )

        if not nodes:
            #print 'add_timeout, now = %s' % now
            tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + 3,
                lambda: self.have_new_node(now) )
        else:
            nodes = self.db.query('SELECT * from node;')
            #print 'go finish, now = %s' % now
            self.render( 'node/dynamic_node_list.html',
                         nodes = nodes )
