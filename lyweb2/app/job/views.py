# coding: utf-8

import logging, datetime, time
import tornado
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous


class Index(LyRequestHandler):

    def get(self):

        LYJOB_ACTION = self.application.settings['LYJOB_ACTION']

        jobs = self.db.query('SELECT * from job;')
        for j in jobs:
            j.user = self.db.get(
                'SELECT * from auth_user WHERE id=%s;',
                j.user_id )

            j.action_str = 'unknown'

            for k, v in LYJOB_ACTION.items():
                if v == j.action:
                    j.action_str = k
                    break;

        d = { 'title': 'Servers Home', 'jobs': jobs }

        self.render('job/index.html', **d)


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


