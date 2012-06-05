# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.instance.models import Instance

from lycustom import has_permission


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
        instances = self.db2.query(Instance).order_by('id').all()
        self.render( 'admin/instance/index.html',
                     title = _('Instance Management'),
                     INSTANCE_LIST = instances )


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




