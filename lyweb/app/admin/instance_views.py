# coding: utf-8

import logging, datetime, time, re, json
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.instance.models import Instance
from app.appliance.models import Appliance
from app.job.models import Job
from app.node.models import Node

from settings import JOB_TARGET

from lycustom import has_permission
from ytool.pagination import pagination

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
                self.write( self.trans(_('No such instance : %s')) % instance_id )
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
            self.write( self.trans(_('Wrong action value!')) )


    def post(self):

        if not self.action:
            self.write( self.trans(_('No action found !')) )

        elif self.action == 'change_owner':
            self.change_owner()

        else:
            self.write( self.trans(_('Wrong action value!')) )

    def get_index(self):

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 1)
        status = self.get_argument_int('status', -1)
        user_group = self.get_argument_int('user_group', -1)
        page_size = self.get_argument_int('sepa', 50)
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

        U = None
        if (user_group <= 0) and uid:
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

        # Group filter
        if user_group > 0:
            ug = self.db2.query(Group).get(user_group)
            if ug:
                instances = instances.join(
                    Instance.user).join(User.groups).filter(
                    User.groups.contains(ug) )

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

        page_html = pagination(self.request.uri, total, page_size, cur_page, sepa_range=[20, 50, 100])

        def sort_by(by):
            return self.urlupdate(
                {'by': by, 'order': 1 if order == 0 else 0, 'p': 'dropthis'})

        d = { 'title': self.trans(_('Instance Management')),
              'urlupdate': self.urlupdate,
              'sort_by': sort_by, 'SORTBY': by,
              'INSTANCE_LIST': instances, 'TOTAL_INSTANCE': total,
              'PAGE_HTML': page_html,
              'SORT_USER': U, 'SORT_APPLIANCE': APPLIANCE,
              'SORT_NODE': NODE, 'STATUS': status,
              'INSTANCE_STATUS': INSTANCE_STATUS_SHORT_STR,
              'USER_GROUP_ID': user_group, 'GROUP_LIST': self.db2.query(Group) }

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

        d = { 'title': self.trans(_('View Instance "%s"')) % I.name,
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
            return self.write( self.trans(_('Unknown action "%s" !')) % action )

        LYJOB_ACTION = self.settings['LYJOB_ACTION']
        action_id = LYJOB_ACTION.get(action, 0)

        JID_LIST = []

        for I in INSTANCE_LIST:
            jid = self.new_job(JOB_TARGET['INSTANCE'], I.id, action_id)
            JID_LIST.append(jid)

        self.write( self.trans(_('%(action)s all instance success: %(jid_list)s')) % {
                'action': action, 'jid_list': JID_LIST } )


    def change_owner(self):

        I = self.instance

        d = { 'title': self.trans(_('Change owner of instance')), 'I': I }
        
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
                    E.append( self.trans(_('Can not find user: %s')) % user )
            else:
                E.append( self.trans(_('No user input !')) )

            reason = self.get_argument('reason', '')

            if E:
                d['ERROR'] = E
            else:
                T = self.lytrace(
                    ttype = LY_TARGET['INSTANCE'], tid = I.id,
                    do = self.trans(_('change instance owner %(old_owner)s to %(new_owner)s')) % {
                        'old_owner': I.user.username, 'new_owner': U.username } )

                I.user = U
                self.db2.commit()
                # TODO: send reason to user
                url = self.reverse_url('admin:instance')
                url += '?id=%s' % I.id
                return self.redirect( url )

        self.render( 'admin/instance/change_owner.html', **d)
