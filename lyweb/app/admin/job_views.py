# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.job.models import Job

from sqlalchemy.sql.expression import asc, desc

from lycustom import has_permission

from ytool.pagination import pagination


class JobManagement(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.job = None
        self.action = self.get_argument('action', 'index')

        job_id = self.get_argument('id', 0)
        if job_id:
            self.job = self.db2.query(Job).get( job_id )
            if not self.job:
                self.write( self.trans(_('No such node')) % job_id )
                return self.finish()


    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'view':
            self.get_view()

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def post(self):

        if not self.action:
            self.write( self.trans(_('No action found !')) )

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def get_index(self):

        user_id = self.get_argument_int('user', 0)
        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 1)

        if by not in [ 'id', 'user_id', 'status', 'target_type',
                       'target_id', 'action', 'created', 'started',
                       'ended' ]:
            by = 'id'

        order_func = desc( by ) if order else asc( by )

        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        JOB_LIST = self.db2.query(Job)

        U = None
        if user_id:
            U = self.db2.query(User).get(user_id)
            JOB_LIST = JOB_LIST.filter(Job.user_id == user_id)
        JOB_LIST = JOB_LIST.order_by( order_func ).slice(start, stop)

        JOB_TOTAL = self.db2.query(Job.id).count()

        page_html = pagination(self.request.uri, JOB_TOTAL,
                               page_size, cur_page,
                               sepa_range = [20, 50, 100])

        def sort_by(by):
            return self.urlupdate(
                {'by': by, 'order': 1 if order == 0 else 0, 'p': 1})

        d = { 'title': 'Jobs', 'U': U,
              'sort_by': sort_by,
              'JOB_TOTAL': JOB_TOTAL,
              'JOB_LIST': JOB_LIST,
              'page_html': page_html }

        self.render('admin/job/index.html', **d)
