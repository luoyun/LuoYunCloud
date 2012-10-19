# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.instance.models import Instance
from app.appliance.models import Appliance

from lycustom import has_permission

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_


class InstanceManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.instance = None
        self.action = self.get_argument('action', 'index')

        instance_id = self.get_argument('id', 0)
        if instance_id:
            self.instance = self.db2.query(Instance).get( instance_id )
            if not self.instance:
                self.write( _('No such instance : %s') % instance_id )
                return self.finish()


    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action in ['stop_all', 'start_all']:
            self.get_control_all(self.action)

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        else:
            self.write( _('Wrong action value!') )

    def get_index(self):

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'desc')
        status = self.get_argument('status', 'all')
        page_size = int(self.get_argument('sepa', 30))
        cur_page = int(self.get_argument('p', 1))
        uid = int(self.get_argument('uid', 0)) # sort by user
        aid = int(self.get_argument('aid', 0)) # sort by appliance

        start = (cur_page - 1) * page_size
        stop = start + page_size

        instances = self.db2.query(Instance)

        if status != 'all':
            if status == 'stoped':
                slist = settings.INSTANCE_SLIST_STOPED
            else: # show running
                slist = settings.INSTANCE_SLIST_RUNING
            instances = instances.filter(Instance.status.in_( slist))

        U = self.db2.query(User).get( uid )
        if U:
            instances = instances.filter_by( user_id = uid )

        APPLIANCE = self.db2.query(Appliance).get( aid )
        if APPLIANCE:
            instances = instances.filter_by( appliance_id = aid )

        if by == 'created':
            by_obj = Instance.created
        elif by == 'updated':
            by_obj = Instance.updated
        else:
            by_obj = Instance.id


        sort_by_obj = desc(by_obj) if sort == 'desc' else asc(by_obj)

        instances = instances.order_by( sort_by_obj )

        # TODO: may have a more highly active count ( use id )
        total = instances.count()

        instances = instances.slice(start, stop)

        if total > page_size:
            page_html = Pagination(
                total = total,
                page_size = page_size,
                cur_page = cur_page ).html(self.get_page_url)
        else:
            page_html = ""

        d = { 'title': _('Instance Management'),
              'INSTANCE_LIST': instances, 'TOTAL_INSTANCE': total,
              'PAGE_HTML': page_html,
              'SORT_USER': U, 'SORT_APPLIANCE': APPLIANCE }

        self.render( 'admin/instance/index.html', **d )


    def get_control_all(self, action):

        if action == 'stop_all':
            action = 'stop'
            INSTANCE_LIST = self.db2.query(Instance).filter( Instance.status != 2 )

        elif action == 'start_all':
            action = 'run'
            INSTANCE_LIST = self.db2.query(Instance).filter_by( status = 2 )

        else:
            return self.write( _('Unknown action "%s" !') % action )

        LYJOB_ACTION = self.settings['LYJOB_ACTION']
        action_id = LYJOB_ACTION.get(action, 0)

        JID_LIST = []

        for I in INSTANCE_LIST:
            jid = self.new_job(JOB_TARGET['INSTANCE'], I.id, action_id)
            JID_LIST.append(jid)

        self.write( _('%s all instance success: %s') % ( action, JID_LIST ) )




