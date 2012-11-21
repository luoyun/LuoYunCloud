# coding: utf-8

import logging, datetime, time, re, json
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.instance.models import Instance
from app.appliance.models import Appliance
from app.job.models import Job
from app.node.models import Node

from settings import JOB_TARGET

from lycustom import has_permission

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_

import settings
from settings import INSTANCE_DELETED_STATUS as DELETED_S
from settings import LY_TARGET

from app.instance.models import INSTANCE_STATUS_SHORT_STR


class InstanceManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.instance = None
        self.action = self.get_argument('action', 'index')

        instance_id = self.get_argument('id', 0)
        if instance_id:
            self.instance = self.db2.query(Instance).get( instance_id )
            if self.instance and self.action == 'index':
                self.action = 'view'
            elif not self.instance:
                self.write( _('No such instance : %s') % instance_id )
                return self.finish()


    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'view':
            self.get_view()

        elif self.action == 'change_owner':
            self.change_owner()

        elif self.action in ['stop_all', 'start_all']:
            self.get_control_all(self.action)

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        elif self.action == 'change_owner':
            self.change_owner()

        else:
            self.write( _('Wrong action value!') )

    def get_index(self):

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 0)
        status = self.get_argument_int('status', -1)
        page_size = self.get_argument_int('sepa', 30)
        cur_page = self.get_argument_int('p', 1)
        uid = self.get_argument_int('uid', 0) # sort by user
        aid = self.get_argument_int('aid', 0) # sort by appliance
        nid = self.get_argument_int('node', 0) # sort by node

        start = (cur_page - 1) * page_size
        stop = start + page_size

        instances = self.db2.query(Instance)

        if status not in [k for k,v in INSTANCE_STATUS_SHORT_STR]:
            status = -1

        if status == -1:
            instances = instances.filter(
                Instance.status != DELETED_S )
        else:
            instances = instances.filter(Instance.status==status)

        U = self.db2.query(User).get( uid )
        if U:
            instances = instances.filter_by( user_id = uid )

        APPLIANCE = self.db2.query(Appliance).get( aid )
        if APPLIANCE:
            instances = instances.filter_by( appliance_id = aid )

        if nid:
            NODE = self.db2.query(Node).get( nid )
            if NODE:
                instances = instances.filter_by( node_id = nid )
        else:
            NODE = None

        if by == 'created':
            by_obj = Instance.created
        elif by == 'updated':
            by_obj = Instance.updated
        elif by == 'node':
            by_obj = Instance.node_id
        elif by == 'user':
            by_obj = Instance.user_id
        elif by == 'appliance':
            by_obj = Instance.appliance_id
        elif by == 'status':
            by_obj = Instance.status
        elif by == 'name':
            by_obj = Instance.name
        else:
            by_obj = Instance.id


        sort_by_obj = desc(by_obj) if order else asc(by_obj)

        instances = instances.order_by( sort_by_obj )

        # TODO: may have a more highly active count ( use id )
        total = instances.count()

        instances = instances.slice(start, stop).all()

        if total > page_size:
            page_html = Pagination(
                total = total,
                page_size = page_size,
                cur_page = cur_page ).html(self.get_page_url)
        else:
            page_html = ""

        d = { 'title': _('Instance Management'),
              'urlupdate': self.urlupdate,
              'INSTANCE_LIST': instances, 'TOTAL_INSTANCE': total,
              'PAGE_HTML': page_html,
              'ORDER': 1 if order == 0 else 0,
              'SORT_USER': U, 'SORT_APPLIANCE': APPLIANCE,
              'SORT_NODE': NODE, 'STATUS': status,
              'INSTANCE_STATUS': INSTANCE_STATUS_SHORT_STR }

        self.render( 'admin/instance/index.html', **d )


    def get_view(self):

        I = self.instance

        tab = self.get_argument('tab', 'general')

        JOB_LIST = self.db2.query(Job).filter(
            Job.target_id == I.id,
            Job.target_type == JOB_TARGET['INSTANCE']
            ).order_by( desc(Job.id) )
        JOB_LIST = JOB_LIST.limit(10);

        config = json.loads(I.config) if I.config else {}

        network = config.get('network', [])

        password = config.get('passwd_hash')

        storage = config.get('storage', [])
        webssh = config.get('webssh', None)

        d = { 'title': _('View Instance "%s"') % I.name,
              'I': I, 'JOB_LIST': JOB_LIST, 'NETWORK_LIST': network,
              'STORAGE_LIST': storage,
              'webssh': webssh, 'TAB': tab }

        self.render( 'admin/instance/view.html', **d )


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


    def change_owner(self):

        I = self.instance

        d = { 'title': _('Change owner of instance'), 'I': I }
        
        E = []
        U = None
        
        if self.request.method == 'POST':
            user = self.get_argument('user', 0)
            if user:
                if user.isdigit():
                    U = self.db2.query(User).get(user)
                if not U:
                    U = self.db2.query(User).filter_by(username=user).first()
                if not U:
                    E.append( _('Can not find user: %s') % user )
            else:
                E.append( _('No user input !') )

            reason = self.get_argument('reason', '')

            if E:
                d['ERROR'] = E
            else:
                T = self.lytrace(
                    ttype = LY_TARGET['INSTANCE'], tid = I.id,
                    do = _('change instance owner %s to %s') % (
                        I.user.username, U.username) )

                I.user = U
                self.db2.commit()
                # TODO: send reason to user
                url = self.reverse_url('admin:instance')
                url += '?id=%s' % I.id
                return self.redirect( url )

        self.render( 'admin/instance/change_owner.html', **d)
