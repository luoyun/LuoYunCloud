# coding: utf-8

import struct, socket
import logging, datetime, time
import tornado
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from settings import JOB_ACTION, JOB_TARGET


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



class Action(LyRequestHandler):

    @authenticated
    def get(self, id):

        action = int(self.get_argument("action", 0))

        node = self.db.get('SELECT * FROM node WHERE id=%s;', id)

        if not node:
            return self.write('No such node!')

        if not action:
            return self.render('node/view.html', node=node)

        elif action == 1:
            if node.isenable:
                return self.write('Already enable !')
            else:
                self.new_job(JOB_TARGET['NODE'], id, JOB_ACTION['ENABLE_NODE'])

        elif action == 2:
            if not node.isenable:
                return self.write('Already disable !')
            else:
                self.new_job(JOB_TARGET['NODE'], id, JOB_ACTION['DISABLE_NODE'])
        else:
            return self.write('Unknow action!')

        return self.write('Action success !')
