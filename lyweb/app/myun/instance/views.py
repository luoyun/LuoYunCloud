import logging
import json
import datetime

from sqlalchemy import asc, desc, and_
from tornado.web import authenticated

from app.instance.models import Instance
from app.storage.models import StoragePool, Storage
from app.network.models import NetworkPool, IPPool, \
    Gateway, PortMapping
from app.account.models import PublicKey
from app.domain.models import UserDomain
from app.appliance.models import Appliance
from app.job.models import Job

from .forms import PublicKeyForm, BaseinfoForm, StorageForm, \
    ResourceForm, NetworkForm, PasswordSetForm, \
    InstancePasswordForm, InstancePublicKeyForm, \
    InstanceDomainForm, \
    InstanceCreateBaseForm, InstanceCreateForm, \
    PortMappingForm

from lycustom import RequestHandler, has_permission
from ytool.pagination import pagination
from lytool.filesize import size as human_size
from tool.firewall import Prerouting

from app.system.utils import add_trace

import settings
from settings import INSTANCE_DELETED_STATUS as DELETED_S
from settings import JOB_TARGET



class Index(RequestHandler):

    title = _('My Instances')

    @authenticated
    def get(self):

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'desc')
        status = self.get_argument('status', 'all')
        page_size = self.get_argument_int(
                'sepa', settings.MYUN_INSTANCE_LIST_PAGE_SIZE)
        cur_page = self.get_argument_int('p', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        if status == 'running':
            slist = settings.INSTANCE_SLIST_RUNING
        elif status == 'stoped':
            slist = settings.INSTANCE_SLIST_STOPED
        else:
            slist = None

        if slist:
            instances = self.db.query(Instance).filter(
                Instance.status.in_( slist) ).filter_by(
                user_id = self.current_user.id )
        else:
            instances = self.db.query(Instance).filter(
                Instance.status != DELETED_S ).filter_by(
                user_id = self.current_user.id )

        # TODO: does this work ?
        if by == 'created':
            by_obj = Instance.created
        elif by == 'username':
            by_obj = Instance.user.username
        else:
            by_obj = Instance.id

        sort_by_obj = desc(by_obj) if sort == 'desc' else asc(by_obj)

        instances = instances.order_by( sort_by_obj )

        total = instances.count()
        instances = instances.slice(start, stop).all()

        page_html = pagination(self.request.uri, total, page_size, cur_page)


        d = { 'INSTANCE_LIST': instances, 'page_html': page_html }

        self.render( 'myun/instance/index.html', **d)



class InstanceActionHandler(RequestHandler):

    def set_myinstance(self):

        self.I = None

        ID = self.get_argument_int('id', 0)
        if not ID:
            return self.write( _('Give the instance id please.') )
        
        I = self.db.query(Instance).get(ID)

        if I:
            if I.status == DELETED_S:
                return self.write( _('Instance %s was deleted') % ID )
            else:
                if ( self.current_user.id != I.user_id ):
                    return self.write( _("Not your instance") )
        else:
            return self.write( _('No such instance: %s') % ID )

        self.I = I
        self.prepare_kwargs['I'] = I
        self.prepare_kwargs['human_size'] = human_size


    def get_instance_lastjob(self, I):

        lastjob = self.db.query(Job).filter(
            and_( Job.target_type == JOB_TARGET['INSTANCE'],
                  Job.target_id == I.id ) ).order_by(
            desc( Job.id ) ).first()

        return lastjob



class View(InstanceActionHandler):

    @authenticated
    def get(self):

        self.set_myinstance()

        I = self.I

        if not I:
            return

        lastjob = self.get_instance_lastjob( I )

        portmapping_list = []
        for IP in I.ips:
            portmapping_list.extend(
                self.db.query(PortMapping).filter_by(
                    ip_id = IP.id).all() )

        d = { 'title': _('View instance "%s"') % I.name,
              'lastjob': lastjob,
              'portmapping_list': portmapping_list  }

        self.render( 'myun/instance/view.html', **d)



class GlobalPasswordEdit(RequestHandler):

    title = _('Configure Global Password For Instances')
    template_path = 'myun/instance/global_password_edit.html'

    @authenticated
    def prepare(self):

        self.form = PasswordSetForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form

        if form.validate():

            profile = self.current_user.profile

            profile.set_root_password( form.password.data )
            self.db.commit()

            url = self.reverse_url('myun:instance')
            return self.redirect( url )

        self.render()



class ResourceEdit(InstanceActionHandler):

    title = _('Configure Instance Resource')
    template_path = 'myun/instance/resource_edit.html'

    @authenticated
    def prepare(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        self.form = ResourceForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):

        form = self.form
        I = self.I

        form.cpus.data = I.cpus
        form.memory.data = I.memory

        self.render()


    def post(self):

        form = self.form
        I = self.I

        if form.validate():

            I.cpus = form.cpus.data
            I.memory = form.memory.data

            if I.is_running:
                I.ischanged = True

            self.db.commit()

            url = self.reverse_url('myun:instance:view')
            url += '?id=%s' % I.id
            return self.redirect( url )

        self.render()



class BaseinfoEdit(InstanceActionHandler):

    title = _('Configure general info for instance')
    template_path = 'myun/instance/general_edit.html'

    @authenticated
    def prepare(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        self.form = BaseinfoForm(self)
        self.prepare_kwargs['form'] = self.form

    def get(self):

        I = self.I
        form = self.form

        form.name.data = I.name
        form.summary.data = I.summary
        form.description.data = I.description

        self.render()


    def post(self):

        I = self.I
        form = self.form

        if form.validate():
            I.name = form.name.data
            I.summary = form.summary.data
            I.description = form.description.data
            I.updated = datetime.datetime.now()
            self.db.commit()

            url = self.reverse_url('myun:instance:view')
            url += '?id=%s' % I.id
            return self.redirect( url )

        self.render()



class StorageAdd(InstanceActionHandler):

    title = _('Add storage for instance')
    template_path = 'myun/instance/storage_add.html'

    # TODO
    max_storage = 1

    @authenticated
    def prepare(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        if len(self.I.storages) >= self.max_storage:
            self.write( _('Can not add storages any more.') )
            return self.finish()

        pool_list = []
        for P in self.db.query(StoragePool):
            pool_list.append(
                (str(P.id), '%s (%sG)' % (P.name, P.total)) )

        form = StorageForm(self)
        form.pool.choices = pool_list

        self.prepare_kwargs['form'] = form

    def get(self):

        I = self.I

        form = self.prepare_kwargs['form']
        form.process()

        self.render()


    def post(self):

        I = self.I
        form = self.prepare_kwargs['form']

        if form.validate():

            new = Storage( size = form.size.data,
                           pool = form._pool, instance = I )
            self.db.add(new)
            self.db.commit()

            new.pool.update_used()
        
            url = self.reverse_url('myun:instance:view')
            url += '?id=%s' % I.id
            return self.redirect( url )

        self.render()



class StorageActionHandler(RequestHandler):

    def initialize(self):
        ID = self.get_argument_int('id', 0)
        if not ID:
            return self.write( _('Give me the storage id please.') )

        storage = self.db.query(Storage).get( ID )
        if not storage:
            return self.write( _('Can not find storage %s') % ID )

        if storage.instance.user_id != self.current_user.id:
            return self.write( _("Not your instance's storage.") )

        pool_list = []
        for P in self.db.query(StoragePool):
            pool_list.append( (str(P.id), P.name) )

        form = StorageForm(self)
        form.pool.choices = pool_list

        self.prepare_kwargs['storage'] = storage
        self.prepare_kwargs['form'] = form


class StorageEdit(StorageActionHandler):

    title = _('Configure storage for instance')
    template_path = 'myun/instance/storage_add.html'

    @authenticated
    def prepare(self):
        if not self.prepare_kwargs.get('storage', None):
            return self.finish()

    def get(self):

        storage = self.prepare_kwargs['storage']
        form = self.prepare_kwargs['form']

        form.pool.default = storage.pool_id
        form.process()

        form.size.data = storage.size

        self.render()


    def post(self):

        storage = self.prepare_kwargs['storage']
        I = storage.instance

        form = self.prepare_kwargs['form']

        if form.validate():

            if storage.size > form.size.data:
                form.size.errors.append(
                    _('Can not support grow down storage now.') )
                form.size.data = storage.size
            else:
                storage.size = form.size.data
                storage.pool = form._pool

                self.db.add( storage )
                self.db.commit()

                storage.pool.update_used()

                url = self.reverse_url('myun:instance:view')
                url += '?id=%s' % I.id
                return self.redirect( url )

        self.render()


class StorageDelete(StorageActionHandler):

    title = _('Delete instance storage')

    @authenticated
    def get(self):

        storage = self.prepare_kwargs.get('storage', None)

        if not storage:  return

        I = storage.instance

        if not I:
            return self.write( _('No binding instance.') )

        pool = storage.pool

        self.db.delete( storage )
        self.db.commit()

        pool.update_used()
        
        url = self.reverse_url('myun:instance:view')
        url += '?id=%s' % I.id
        self.redirect( url )



class NetworkAdd(InstanceActionHandler):

    title = _('Add network for instance')
    template_path = 'myun/instance/network_add.html'

    # TODO
    max_network = 1

    @authenticated
    def prepare(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        if len(self.I.ips) >= self.max_network:
            self.write( _('Can not add network any more.') )
            return self.finish()

        pool_list = []
        for P in self.db.query(NetworkPool):
            pool_list.append(
                (str(P.id), '%s' % P.name) )

        form = NetworkForm(self)
        form.pool.choices = pool_list

        self.prepare_kwargs['form'] = form

    def get(self):

        form = self.prepare_kwargs['form']
        form.process()

        self.render()


    def post(self):

        I = self.I
        form = self.prepare_kwargs['form']

        if form.validate():
            IP = form._free_ip
            if IP and not IP.instance_id:
                IP.instance_id = I.id
                self.db.commit()

                I.update_network()
                self.db.commit()

                msg = _('get ip %(ip)s for instance %(id)s manually.') % {
                    'ip': IP.ip, 'id': I.id }

                add_trace(self, ttype='IP', tid=IP.id, do=msg)

                url = self.reverse_url('myun:instance:view')
                url += '?id=%s' % I.id
                return self.redirect( url )

        self.render()



class NetworkActionHandler(RequestHandler):

    def initialize(self):
        ID = self.get_argument_int('id', 0)
        if not ID:
            return self.write( _('Give me the network id please.') )

        IP = self.db.query(IPPool).get( ID )
        if not IP:
            return self.write( _('Can not find network %s') % ID )

        if ( IP.instance_id and
             IP.instance.user_id != self.current_user.id ):
            return self.write( _("Not your instance's network.") )

        self.prepare_kwargs['IP'] = IP



class NetworkDelete(NetworkActionHandler):

    title = _('Delete instance network')

    @authenticated
    def get(self):

        IP = self.prepare_kwargs.get('IP', None)
        if not IP:
            return

        I = IP.instance

        if not I:
            return self.write( _('No binding instance.') )

        IP.instance_id = None
        self.db.commit()

        msg = _('free ip %(ip)s from instance %(id)s manually.') % {
            'ip': IP.ip, 'id': I.id }
        add_trace(self, ttype='IP', tid=IP.id, do=msg)

        I.update_network()
        self.db.commit()

        url = self.reverse_url('myun:instance:view')
        url += '?id=%s' % I.id
        self.redirect( url )



class InstancePasswordEdit(InstanceActionHandler):

    title = _('Configure Password For Instances')
    template_path = 'myun/instance/password_edit.html'

    @authenticated
    def prepare(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        self.form = InstancePasswordForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form

        if form.validate():

            if form.usedefault.data:
                passwd = self.I.user.profile.get('secret', {}).get(
                    'root_shadow_passwd', '')
                self.I.set('passwd_hash', passwd)
            else:
                self.I.set_root_password( form.password.data )

            self.I.set('use_global_passwd', form.usedefault.data)
            self.db.commit()

            url = self.reverse_url('myun:instance:view')
            url += '?id=%s' % self.I.id
            return self.redirect( url )

        self.render()



class InstancePublicKeyEdit(InstanceActionHandler):

    title = _('Configure Public Key For Instances')
    template_path = 'myun/instance/public_key_edit.html'

    @authenticated
    def prepare(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        self.form = InstancePublicKeyForm(self)
        self.prepare_kwargs['form'] = self.form

        key_list = []
        for K in self.db.query(PublicKey).filter_by(
            user_id = self.current_user.id):
            key_list.append(
                (str(K.id), '%s' % K.name) )


        self.prepare_kwargs['key_count'] = len(key_list)

        self.form.key.choices = key_list


    def get(self):
        self.render()


    def post(self):

        form = self.form

        if form.validate():

            self.I.set('public_key', form._key.data)
            self.db.commit()

            url = self.reverse_url('myun:instance:view')
            url += '?id=%s' % self.I.id
            return self.redirect( url )

        self.render()



class DomainAdd(InstanceActionHandler):

    title = _('Add Domain For Instance')
    template_path = 'myun/instance/domain_edit.html'

    @authenticated
    def prepare(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        self.form = InstanceDomainForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form

        if form.validate():

            D = self.db.query(UserDomain).filter_by(
                domain = form.domain.data ).first()

            if D:
                form.domain.errors.append(_('This domain exist.'))

            else:
                new = UserDomain( domain = form.domain.data,
                                  user = self.current_user,
                                  instance = self.I )
                self.db.add( new )
                self.db.commit()

                domain = self.I.get('domain', {})
                domain['ip'] = self.I.access_ip
                domain['domain'] = form.domain.data
                self.I.set('domain', domain)
                self.db.commit()

                url = self.reverse_url('myun:instance:view')
                url += '?id=%s' % self.I.id
                return self.redirect( url )

        self.render()



class DomainActionHandler(RequestHandler):

    def initialize(self):

        self.domain =None

        ID = self.get_argument_int('id', 0)
        if not ID:
            return self.write( _('Give me the domain id please.') )

        domain = self.db.query(UserDomain).get( ID )
        if not domain:
            return self.write( _('Can not find domain %s') % ID )

        if domain.instance.user_id != self.current_user.id:
            return self.write( _("Not your domain.") )

        self.prepare_kwargs['domain'] = domain
        self.domain = domain


class DomainDelete(DomainActionHandler):

    title = _('Delete instance domain')

    @authenticated
    def get(self):

        domain = self.domain

        if not domain:  return

        I = domain.instance


        self.db.delete(domain)
        self.db.commit()

        url = self.reverse_url('myun:instance:view')
        url += '?id=%s' % I.id
        self.redirect( url )



class DomainEdit(DomainActionHandler):

    title = _('Edit Domain For Instance')
    template_path = 'myun/instance/domain_edit.html'

    @authenticated
    def prepare(self):

        if not self.domain:
            return self.finish()

        self.form = InstanceDomainForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.form.domain.data = self.domain.domain
        self.render()


    def post(self):

        form = self.form
        D = self.domain
        I = self.domain.instance

        if form.validate():

            isexist = False

            for old in self.db.query(UserDomain).filter_by(
                domain = form.domain.data ):
                if old.id != D.id:
                    isexist = True

            if isexist:
                form.domain.errors.append(_('This domain exist.'))

            else:
                D.domain = form.domain.data
                self.db.commit()

                domain = I.get('domain', {})
                domain['ip'] = I.access_ip
                domain['domain'] = form.domain.data
                I.set('domain', domain)
                self.db.commit()

                url = self.reverse_url('myun:instance:view')
                url += '?id=%s' % I.id
                return self.redirect( url )

        self.render()



class InstanceCreate(RequestHandler):

    title = _('Create new instance')
    template_path = 'myun/instance/create.html'

    @has_permission('instance.create')
    def prepare(self):

        self.A = None

        ID = self.get_argument_int('appliance_id', None)
        if ID:
            A = self.db.query(Appliance).get( ID )

            if ( A and A.isprivate and
                 self.current_user.id != A.user_id ):
                self.write( _('Appliance %s is private.') % ID )
                return self.finish()

            if A and not A.isuseable:
                self.write( _('Appliance %s is locked.') % ID )
                return self.finish()

            self.A = A

        profile = self.current_user.profile
        if not profile:
            self.write( _('System Error: have not find user profile.') )
            return self.finish()

        if not ( profile.cpu_remain >= 1 and
                 profile.memory_remain >= 64 and
                 profile.instance_remain >= 1 ):

            url = self.get_no_resource_url() + "?reason=Resource Limit"
            return self.redirect( url )

        if self.A:
            form = InstanceCreateBaseForm(self)
        else:
            form = InstanceCreateForm(self)

            app_list = []
            for x in self.db.query(Appliance).filter(
                and_( Appliance.isprivate == False,
                      Appliance.isuseable == True ) ):
                app_list.append( ( str(x.id), x.name ) )

#            if len(app_list) < 1:
#                self.write( _('No available appliance now.') )
#                return self.finish()

            form.appliance.choices = app_list

        self.prepare_kwargs['form'] = form
        self.prepare_kwargs['appliance'] = self.A

        self.form = form


    def get(self):

        if self.A:
            self.form.name.data = self.A.name

        self.render()


    def post(self):

        A = self.A
        form = self.form

        if form.validate():

            if not A:
                A = self.db.query(Appliance).get(form.appliance.data)

            if not A:
                return self.write( _('Give me the appliance please.') )

            # Create new instance
            I = Instance( name = form.name.data,
                          user = self.current_user,
                          appliance = A )

            I.cpus = form.cpus.data
            I.memory = form.memory.data
            I.isprivate = form.isprivate.data

            self.db.add( I )
            self.db.commit()

#            I.save_logo()

            # TODO: ip
            self.set_ip( I )

            # TODO: root password
            self.set_secret( I )

            url = self.reverse_url('myun:instance:view')
            url += '?id=%s' % I.id
            return self.redirect(url)

        # Something is wrong
        self.render()


    def set_ip(self, I):

        pool_count = self.db.query(NetworkPool.id).count()
        if pool_count < 1:
            logging.warning('Have not find available network pool.')
            return

        # TODO: get the default network pool
        free_ip = None
        for pool in self.db.query(NetworkPool):
            free_ip = pool.get_free_ip()
            if free_ip:
                break

        if not ( free_ip and not free_ip.instance_id ):
            logging.warning('Have not find available ip.')
            return

        free_ip.instance_id = I.id
        self.db.commit()

        I.update_network()
        self.db.commit()

        msg = _('get ip %(ip)s for instance %(id)s') % {
            'ip': free_ip.ip, 'id': I.id }

        add_trace(self, ttype='IP', tid=free_ip.id, do=msg)
        self.db.commit()


    def set_secret(self, I):

        # password
        passwd = self.current_user.profile.get_root_password()
        if passwd:
            I.set('passwd_hash', passwd)
            I.set('use_global_passwd', True)
            self.db.commit()

        # ssh key
        key_data = None
        for K in self.db.query(PublicKey).filter_by(
            user_id = self.current_user.id ):
            key_data = K.data
            break
        if key_data:
            I.set('public_key', key_data)
            self.db.commit()



class PortMappingAdd(InstanceActionHandler):

    title = _('Add Port Mapping For Instance')
    template_path = 'myun/instance/portmapping_add.html'

    @authenticated
    def prepare(self):

        if self.db.query(Gateway.id).count() < 1:
            error = _('The system have not configure gateway yet.')
            return self.render( error = error )

        self.set_myinstance()

        if not self.I:
            return self.finish()

        ip_list = []
        for IP in self.I.ips:
            ip_list.append( (str(IP.id), '%s' % IP.ip) )

        form = PortMappingForm(self)
        form.ip.choices = ip_list

        self.prepare_kwargs['form'] = form


    def get(self):

        form = self.prepare_kwargs['form']
        form.process()

        self.render()


    def post(self):
        form = self.prepare_kwargs['form']

        if form.validate():

            # TODO: find a useable gateway
            gateway = self.db.query(Gateway).first()

            FP = gateway.get_free_port()
            if FP:
                FP.ip_id = form.ip.data
                FP.ip_port = form.port.data

                self.db.commit()

                self.binding_iptables( FP )

                url = self.reverse_url('myun:instance:view')
                url += '?id=%s' % self.I.id

                return self.redirect( url )

            else:
                form.port.errors.append(
                    _('No free port could be used, contact admin please.') )

        self.render()

    def binding_iptables(self, FP):

        prerouting = Prerouting()

        external_ip = FP.gateway.ip
        external_port = FP.gateway_port
        inner_ip = FP.ip.ip
        inner_port = FP.ip_port

        prerouting.add( external_ip, external_port,
                        inner_ip, inner_port )



class PortMappingDelete(InstanceActionHandler):

    @authenticated
    def get(self):

        self.set_myinstance()

        if not self.I:
            return self.finish()

        portmapping = self.get_argument_int('portmapping', 0)
        if not portmapping:
            return self.write( _('Give me portmapping id please.') )

        pm = self.db.query(PortMapping).get( portmapping )
        if not pm:
            return self.write( _('Can not find portmapping %s') % portmapping )

        if not (pm.ip_id and pm.ip_port):
            return self.write( _('Portmapping %s not binding.') % portmapping )

        if pm.ip not in self.I.ips:
            return self.write( _('Portmapping %s is not for your instance.') % portmapping )

        self.unbinding_iptables( pm )

        pm.ip_port = None
        pm.ip_id = None

        self.db.commit()

        url = self.reverse_url('myun:instance:view')
        url += '?id=%s' % self.I.id

        return self.redirect( url )
        

    def unbinding_iptables(self, FP):

        prerouting = Prerouting()
        prerouting.delete_by_destination(FP.ip.ip, FP.ip_port)
