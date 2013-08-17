# coding: utf-8

import logging, datetime, time, re, json
from lycustom import RequestHandler
from tornado.web import authenticated, asynchronous

from app.auth.models import User, Group, Permission
from app.instance.models import Instance
from app.appliance.models import Appliance
from app.job.models import Job
from app.node.models import Node

from settings import JOB_TARGET

from lycustom import has_permission
from ytool.pagination import pagination

from sqlalchemy.sql.expression import asc, desc, func
from sqlalchemy import and_, or_

import settings
from settings import INSTANCE_DELETED_STATUS as DELETED_S
from settings import LY_TARGET

from app.instance.models import INSTANCE_STATUS_SHORT_STR
from lytool.filesize import size as human_size



class Index(RequestHandler):

    @authenticated
    def get(self):

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'DESC')
        status = self.get_argument_int('status', -1)
        user_group = self.get_argument_int('user_group', -1)
        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)
        uid = self.get_argument_int('uid', 0) # sort by user
        aid = self.get_argument_int('aid', 0) # sort by appliance
        nid = self.get_argument_int('node', 0) # sort by node
        search = self.get_argument('search', False)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        instances = self.db.query(Instance)

        # TODO: more search func
        if search:
            if len(search) > 128: # TODO
                return self.write( _('Too long search text.') )
            sid = self.get_int(search, 0)
            search = '%' + search.lower() + '%'
            if sid:
                instances = instances.filter( or_(
                        func.lower(Instance.name).like(search),
                        Instance.id.in_( [sid] ) ) )
            else:
                instances = instances.filter( or_(
                    func.lower(Instance.name).like(search),
                    ) )

        if status not in [k for k,v in INSTANCE_STATUS_SHORT_STR]:
            status = -1

        if status == -1:
            instances = instances.filter(
                Instance.status != DELETED_S )
        else:
            instances = instances.filter(Instance.status==status)

        U = None
        if (user_group <= 0) and uid:
            U = self.db.query(User).get( uid )
            if U:
                instances = instances.filter_by( user_id = uid )

        APPLIANCE = self.db.query(Appliance).get( aid )
        if APPLIANCE:
            instances = instances.filter_by( appliance_id = aid )

        if nid:
            NODE = self.db.query(Node).get( nid )
            if NODE:
                instances = instances.filter_by( node_id = nid )
        else:
            NODE = None

        # Group filter
        if user_group > 0:
            ug = self.db.query(Group).get(user_group)
            if ug:
                instances = instances.join(
                    Instance.user).join(User.groups).filter(
                    User.groups.contains(ug) )

        if by not in ['created', 'updated', 'node_id', 'user_id',
                      'appliance_id', 'status', 'name', 'id',
                      'tx', 'rx', 'bandwidth', 'extendsize',
                      'memory', 'cpus', 'islocked', 'isprivate',
                      'like', 'unlike', 'visit']:
            by = 'id'

        # TODO: Fix sqlalchemy column bug
        if by == 'id':
            by = Instance.id

        sort_by_obj = desc(by) if sort == 'DESC' else asc(by)

        instances = instances.order_by( sort_by_obj )

        # TODO: may have a more highly active count ( use id )
        total = instances.count()

        instances = instances.slice(start, stop).all()

        page_html = pagination(self.request.uri, total, page_size, cur_page, sepa_range=[20, 50, 100])


        d = { 'title': self.trans(_('Instance Management')),
              'human_size': human_size,
              'urlupdate': self.urlupdate,
              'SORTBY': by, 'SORT': sort,
              'INSTANCE_LIST': instances, 'TOTAL_INSTANCE': total,
              'PAGE_HTML': page_html,
              'SORT_USER': U, 'SORT_APPLIANCE': APPLIANCE,
              'SORT_NODE': NODE, 'STATUS': status,
              'INSTANCE_STATUS': INSTANCE_STATUS_SHORT_STR,
              'USER_GROUP_ID': user_group, 'GROUP_LIST': self.db.query(Group) }

        if self.get_argument('ajax', None):
            self.render( 'admin/instance/index.ajax.html', **d )
        else:
            self.render( 'admin/instance/index.html', **d )



class InstanceManagement(RequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.instance = None
        self.action = self.get_argument('action', 'index')

        instance_id = self.get_argument('id', 0)
        if instance_id:
            self.instance = self.db.query(Instance).get( instance_id )
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


    def get_control_all(self, action):

        if action == 'stop_all':
            action = 'stop'
            INSTANCE_LIST = self.db.query(Instance).filter( Instance.status != 2 )

        elif action == 'start_all':
            action = 'run'
            INSTANCE_LIST = self.db.query(Instance).filter_by( status = 2 )

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
                    U = self.db.query(User).get(user)
                if not U:
                    U = self.db.query(User).filter_by(username=user).first()
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
                self.db.commit()
                # TODO: send reason to user
                url = self.reverse_url('admin:instance')
                url += '?id=%s' % I.id
                return self.redirect( url )

        self.render( 'admin/instance/change_owner.html', **d)



class InstanceHandler(RequestHandler):

    def get_instance(self):

        ID = self.get_argument('id', 0)
        if ID:
            I = self.db.query(Instance).get( ID )
            if I:
                return I

            else:
                self.write( _('Can not find instance %s') % ID )

        else:
            self.write( _('Give me instance id please.') )

        return None



class View(InstanceHandler):

    @has_permission('admin')
    def get(self):

        I = self.get_instance()
        if not I: return


        d = { 'title': _('View Instance "%s"') % I.name,
              'I': I, 'human_size': human_size }

        if self.get_argument('ajax', None):
            self.render('admin/instance/view.ajax.html', **d)
        else:
            self.render('admin/instance/view.html', **d)
