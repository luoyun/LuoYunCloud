# coding: utf-8

import logging, struct, socket, re, os, json, time
from datetime import datetime
from dateutil import relativedelta

from lycustom import RequestHandler
from tornado.web import authenticated, asynchronous
import tornado

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_

from app.appliance.models import Appliance
from app.instance.models import Instance
from app.job.models import Job
from app.system.models import LuoYunConfig
from app.network.models import IPPool

from lycustom import has_permission

import settings
from settings import INSTANCE_DELETED_STATUS as DELETED_S
from settings import JOB_ACTION, JOB_TARGET, LY_TARGET

from ytool.pagination import pagination

from tool.domain import instance_domain_binding, \
    instance_domain_unbinding



class Index(RequestHandler):

    title = _('LuoYunCloud Public Instance Home')

    def get(self):

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'updated')
        order = self.get_argument_int('order', 1)
        status = self.get_argument('status', 'running')
        page_size = self.get_argument_int(
                'sepa', settings.INSTANCE_HOME_PAGE_SIZE)
        cur_page = self.get_argument_int('p', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        if status == 'running':
            slist = settings.INSTANCE_SLIST_RUNING
        elif status == 'stoped':
            slist = settings.INSTANCE_SLIST_STOPED
        else:
            status == 'all'
            slist = settings.INSTANCE_SLIST_ALL

        instances = self.db.query(Instance).filter(
            Instance.isprivate != True ).filter(
            Instance.status.in_( slist) )

        if view == 'self' and self.current_user:
            instances = instances.filter_by(
                user_id = self.current_user.id )

        if by == 'created':
            by_obj = Instance.created
        elif by == 'user':
            by_obj = Instance.user_id
        else:
            by_obj = Instance.updated

        sort_by_obj = desc(by_obj) if order else asc(by_obj)

        instances = instances.order_by( sort_by_obj )

        # TODO: may have a more highly active count ( use id )
        total = instances.count()

        instances = instances.slice(start, stop)

        page_html = pagination(self.request.uri, total, page_size, cur_page)

        d = { 'title': self.title,
              'INSTANCE_LIST': instances,
              'cur_page': cur_page,
              'SORTBY': by, 'ORDER': "0" if order == 0 else "1",
              'STATUS': status, 'VIEW': view,
              'urlupdate': self.urlupdate,
              'page_html': page_html }

        self.render("instance/index.html", **d)



class View(RequestHandler):
    ''' Show Instance's information '''

    def initialize(self):

        self.I = None

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me instance id please.') )

        I = self.db.query(Instance).get( ID )
        if not I:
            return self.write( _('Can not find instance %s') % ID )

        if I.isprivate:
            if ( not self.current_user or
                 ( self.current_user.id != I.user_id and
                   not self.has_permission('admin') ) ):
                return self.write( _('Instance %s is private !') % ID )

        if I.status == DELETED_S:
            return self.write( _('Instance %s is deleted !') % ID )

        self.I = I


    def get(self):

        if not self.I: return

        I = self.I

        d = { 'title': _('Baseinfo of instance %s') % I.id,
              'instance': I }

        self.render('instance/view.html', **d)



class SingleInstanceStatus(RequestHandler):

    ''' check a instance status '''

    @asynchronous
    def post(self):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        ID = self.get_int( self.get_argument('id', 0) )
        I = self.db.query(Instance).get(ID)
        if I:
            self.check_status({
                'instance': I,
                'old_is': self.get_int(self.get_argument('is', 0)),
                'old_js': self.get_int(self.get_argument('js', 0)) })
        else:
            self.write( {'return_code': 1} )
            self.finish()


    def check_status(self, cs):

        if self.request.connection.stream.closed():
            return

        self.db.commit() # TODO: need sync now

        I = cs['instance']
        old_is = cs['old_is']
        old_js = cs['old_js']

        # TODO: hack for test I is exists already.
        try:
            I.id
        except:
            logging.warn('Instance obj is deleted, can not check status.')
            return

        #print '[DD] ID: %s, is: [%s, %s], js: [%s, %s]' % (I.id, old_is, I.status, old_js, I.lastjob_status_id)

        if (
            (old_is and old_is != I.status) or
            (old_js and I.lastjob and old_js != I.lastjob.status) ):

            self.write( self.get_json_data( I ) )
            self.finish()

        else:
            # Need sleep to wait change
            if I.lastjob and not I.lastjob.completed:
                time_interval = settings.INSTANCE_S_UP_INTER_1
            else:
                time_interval = settings.INSTANCE_S_UP_INTER_2
            #print '[DD] %s SLEEP %s seconds' % (datetime.now(), time_interval)

            tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + time_interval,
                lambda: self.check_status(cs) )


    def get_json_data(self, I):

        CS = { 'return_code' : 0,
               'id'          : I.id,

               'is'          : I.status,
               'is_str'      : self.trans(I.status_string),

               'js'          : I.lastjob_status_id,
               'js_str'      : self.trans(I.lastjob_status_string),
               'lastjob'     : I.lastjob_id if I.lastjob_id else 0,

               'vdi_ip'      : I.vdi_ip,
               'vdi_port'    : I.vdi_port,

               'ip'          : '',
               'ip_link'     : '',
               'domain'      : '',
               'domain_link' : '' }

        CS['is_img'] = I.status_icon
        CS['js_img'] = I.lastjob_status_icon

        if I.work_ip:
            CS['ip_link'] = I.home_url(self.current_user, useip=True)
            CS['ip'] = I.work_ip

        if I.domain and I.is_running:
            CS['domain_link'] = I.home_url(self.current_user)
            CS['domain'] = I.domain

        CS['action'] = I.action
        CS['action_trans'] = self.trans( I.action )

        return CS



class LifeHandler(RequestHandler):

    def myfinish(self, status=1, string=None):

        d = { 'code': status,
              'data': [],
              'string': string }

        self.write( d )
        self.finish()
        

    def get_instance(self, ID):

        I = self.db.query(Instance).get(ID)
        if not I:
            return None, _('Can not find instance %s') % ID

        if I.status == DELETED_S:
            return None, _('Instance %s was deleted') % ID

        if self.current_user.id != I.user_id:
            if not self.has_permission('admin'):
                return None, _("No permission for instance %s") % ID

        return I, None
        

    def set_root_passwd(self, I):

        if I.get('use_global_passwd', True):
            x = I.user.profile.get('root_shadow_passwd')
            I.set('passwd_hash', x)


    def binding_domain(self, I):
        # Binding in nginx
        ret, reason = instance_domain_binding(self.db, I)
        if not ret:
            logging.warn(_('binding domain failed: %s') % reason)

        # TODO: update config about domain

        I.update_network()

    def unbinding_domain(self, I):

        # unbinding in nginx
        ret, reason = instance_domain_unbinding(self.db, I)
        if not ret:
            logging.warn(_('unbinding domain failed: %s') % reason)

        # TODO: update config about domain

        I.update_network()


    def run_job(self, I, action_id):

        if I.lastjob and (not I.lastjob.completed):
            if not ( action_id == JOB_ACTION['STOP_INSTANCE'] and
                 I.lastjob.canstop ):
                # TODO: status = 100, timeout > 60s
                timeout = I.lastjob.created + relativedelta.relativedelta(seconds=+60)
                if timeout > datetime.now():
                    return self.trans(_("Previous task is not finished !"))

        # Create new job
        job = Job( user = self.current_user,
                   target_type = JOB_TARGET['INSTANCE'],
                   target_id = I.id,
                   action = action_id )

        self.db.add(job)
        self.db.commit()
        
        I.lastjob = job

        try:
            self._job_notify( job.id )
        except Exception, e:
            #[Errno 113] No route to host
            # TODO: should be a config value
            job.status = settings.JOB_S_FAILED
            return self.trans(_("Connect to control server failed: %s")) % e

        self.db.commit()
        return self.trans(_('Task starts successfully.'))


    # TODO: need a new design.
    def update_user_resource(self, user, I, action, start, timeout):

        if time.time() - start > timeout:
            return

        #logging.info('update_user_resource, i am here, now = %s' % time.time())

        self.db.commit() # TODO: need sync now
        time_interval = 3

        if action == 'run':
            if I.is_running:
                user.profile.update_resource_used()
                return

        elif action == 'stop':
            if not I.is_running:
                user.profile.update_resource_used()
                return

        else:
            time_interval = 10
            user.profile.update_resource_used()


        tornado.ioloop.IOLoop.instance().add_timeout(
            time.time() + time_interval,
            lambda: self.update_user_resource(
                user, I, action, start, timeout) )



class LifeControl(LifeHandler):

    ''' Instance life control: stop/run/reboot/query/delete

    Input:
           id = 1,2,3,4,5,...

    Output:
           { code: 0/1/...,   # 0 is success.
             data: [ { id: 1,
                       code: 0/1/..., # 0 is success.
                       data: "xxx",   # description about code
                     }, {}, ... ]
           }
    '''

    @authenticated
    def post(self):

        # action
        action = self.get_argument('action', '').lower().strip()
        if not action:
            return self.myfinish(
                string = _('Give me the action please.') )

        if action not in ['run', 'stop', 'query', 'reboot', 'delete']:
            return self.myfinish(
                string = _('Just support run/stop/reboot/query action') )

        # id list
        _IDS = self.get_argument('id', '')
        ID_LIST = []

        for x in _IDS.split(','):
            x = x.strip()
            if x:
                ID_LIST.append(x)

        if not ID_LIST:
            return self.myfinish(
                string = _('Instance id list is empty.') )

        # run action
        data = []
        for ID in ID_LIST:
            I, msg = self.get_instance(ID)
            if I:
                _callback = getattr(self, action)
                data.append( _callback( I ) )

                # TODO: a monitor and update
                timeout = 120 # 2 minutes
                start = time.time()
                tornado.ioloop.IOLoop.instance().add_callback(
                    lambda: self.update_user_resource(
                        self.current_user, I, action, start, timeout) )
            else:
                data.append( { 'id': -1, 'code': 1, 'data': msg } )

        status = 0
        for x in data:
            if x['code']:
                status = 1
                break

        # finish
        self.write({'code': status, 'data': data})


    def run(self, I):

        d = { 'id': I.id, 'code': 1, 'data': '' }

        profile = self.current_user.profile

        if not ( profile and
                 profile.cpu_remain >= I.cpus and
                 profile.memory_remain >= I.memory ):

            d['data'] = _('Resource limit: need %(cpus)s CPU, \
%(memory)s, but you have %(cpu_remain)s CPU, %(memory_remain)s.') % {
                'cpus': I.cpus, 'memory': I.memory,
                'cpu_remain': profile.cpu_remain,
                'memory_remain': profile.memory_remain }
            return d

        if I.is_running:
            d['data'] = _('Instance is running now.')
            return d

        # TODO: set passwd
        self.set_root_passwd(I)

        d['data'] = self.run_job(I, JOB_ACTION['RUN_INSTANCE'])
        d['code'] = 0
        d['data'] += ' %s' % self.binding_domain( I )

        return d


    def stop(self, I):

        d = { 'id': I.id, 'code': 1, 'data': '' }
        
        if not I.is_running:
            d['data'] = _('Instance is stopped now.')
            return d

        d['data'] = self.run_job(I, JOB_ACTION['STOP_INSTANCE'])
        d['code'] = 0
        d['data'] += ' %s' % self.unbinding_domain( I )

        return d


    def query(self, I):

        d = { 'id': I.id, 'code': 1, 'data': '' }

        if not I.need_query:
            d['data'] = _('Instance does not need query.')
            return d

        d['data'] = self.run_job(I, JOB_ACTION['QUERY_INSTANCE'])
        d['code'] = 0

        return d


    def delete(self, I):

        d = {'code': 1, 'id': I.id, 'data': ''}
            
        # TODO: no running delete !
        if I.is_running:
            d['data'] = _('Can not delete a running instance!')
            return d

        # TODO: delete domain binding
        d['data'] += ' %s' % self.unbinding_domain( I )

        I.status = DELETED_S
        I.name = '_notexist_%s_' % I.id
        self.db.commit()

        for x in I.ips:
            x.instance_id = None
            x.updated = datetime.now()

            T = self.lytrace(
                ttype = LY_TARGET['IP'], tid = x.id,
                do = _('release ip %(ip)s from instance %(id)s') % {
                    'ip': x.ip, 'id': I.id } )

        self.db.commit()
        
        # delete instance files
        d['data'] += self.run_job(I, JOB_ACTION['DESTROY_INSTANCE'])
        d['code'] = 0

        return d



class AttrSet(RequestHandler):
    ''' set instance attr '''

    @authenticated
    def post(self):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        ID = self.get_argument('id', '')
        ID_LIST = [ self.get_int(x) for x in ID.split(',') ]

        attr = self.get_argument('attr', None)
        value = self.get_argument('value', '').lower().strip()

        d = { 'return_code': 1,
              'success_ids': [],
              'failed_ids': [],
              'retstr_list': [] }

        if not attr:
            d['retstr_list'].append( self.trans(
                    _('No attr find.')) )
            return self.write( d )

        if not value:
            d['retstr_list'].append( self.trans(
                    _('No value find.')) )
            return self.write( d )

        self.attr = attr
        self.value = value

        isadmin = self.has_permission('admin')
        myid = self.current_user.id

        for ID in ID_LIST:

            I = self.db.query(Instance).get(ID)

            if I:
                if ( myid == I.user_id or isadmin ):
                    r = self.set_isprivate( I )
                    if r:
                        d['retstr_list'].append( r )
                        d['failed_ids'].append( ID )
                    else:
                        d['success_ids'].append( ID )
                else:
                    s = _('No permissions to set attr for instance %s.') % ID
                    d['retstr_list'].append( s )
                    d['failed_ids'].append( ID )
            else:
                s = _('Can not find instance %s.') % ID
                d['retstr_list'].append( s )
                d['failed_ids'].append( ID )

        self.db.commit()

        if not d['failed_ids']:
            d['return_code'] = 0

        self.write( d )


    def set_isprivate(self, I):

        if self.value == 'true':
            I.isprivate = True
        elif self.value == 'false':
            I.isprivate = False
        else:
            return self.trans(
                _('Invalid value for attr "isprivate" : %s') % value )


