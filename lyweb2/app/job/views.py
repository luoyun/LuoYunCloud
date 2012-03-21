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


class JobStatus(LyRequestHandler):

    ''' A running job status '''

    @asynchronous
    def get(self, id):

        job = self.db.get(
            'SELECT * FROM job WHERE id=%s;', id )

        if not job:
            self.write(u'No job %s !' % id)
            self.finish()

        previous = int( self.get_argument('previous', 0) )

        self.check_job_status(id, previous)


    def check_job_status(self, id, previous):

        if self.request.connection.stream.closed():
            return

        job = self.db.get(
            'SELECT * FROM job WHERE id=%s;', id )

        #print 'id = %s, previous = %s, now = %s' % (
        #    id, previous, job.status )

        if job.status >= 300 and job.status <= 399:
            json = { 'jid': id, 'job_status': job.status,
                     'desc': self.job_status(job.status),
                     'status': 0 }
            self.write(json)
            return self.finish()

        if job.status == previous:

            tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + 3,
                lambda: self.check_job_status(id, job.status) )

        else:

            json = { 'jid': id, 'job_status': job.status,
                     'desc': self.job_status(job.status),
                     'status': 1 }
            self.write(json)
            self.finish()
