# coding: utf-8

import json, logging
from datetime import datetime
from lycustom import LyRequestHandler

from app.account.models import User, ApplyUser, UserProfile
from app.instance.models import Instance
from app.appliance.models import Appliance, ApplianceCatalog
from app.job.models import Job
from app.system.models import LuoYunConfig, IPPool

from settings import JOB_TARGET

from app.instance.forms import PublicKeyForm, BaseinfoForm, \
     ResourceForm, NetworkForm, StorageForm, PasswordForm, \
     StaticNetworkForm

import tornado
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_

from lytool.filesize import size as human_size
from ytool.pagination import pagination

from tool.domain import get_default_domain

from settings import INSTANCE_DELETED_STATUS as DELETED_S

import settings


class Index(LyRequestHandler):

    @authenticated
    def get(self):

        my = self.db2.query(User).get(self.current_user.id)

        d = { 'my': my, 'human_size': human_size }

        INSTANCE_LIST = self.db2.query(Instance).filter_by(
                user_id = self.current_user.id).filter(
            Instance.status != DELETED_S )

        USED_INSTANCE = INSTANCE_LIST.count()

        TOTAL_APPLIANCE = self.db2.query(Appliance.id).filter_by(
            user_id = self.current_user.id).count()

        TOTAL_CPU = 0
        TOTAL_MEMORY = 0
        TOTAL_INSTANCE = 0


        if self.current_user.profile:
            TOTAL_CPU = self.current_user.profile.cpus
            TOTAL_MEMORY = self.current_user.profile.memory
            TOTAL_INSTANCE = self.current_user.profile.instances
        else:
            TOTAL_CPU = 8
            TOTAL_MEMORY = 4096
            TOTAL_INSTANCE = 20

        USED_CPU = 0
        USED_MEMORY = 0
        USED_STORAGE = 0

        for i in INSTANCE_LIST:
            if i.status in settings.INSTANCE_SLIST_RUNING:
                USED_CPU += i.cpus
                USED_MEMORY += i.memory
                USED_STORAGE += i.storage

        d['title'] = _('My LuoYun')
        d.update({'TOTAL_CPU': TOTAL_CPU,
                  'TOTAL_MEMORY': TOTAL_MEMORY,
                  'USED_CPU': USED_CPU,
                  'USED_MEMORY': USED_MEMORY,
                  'TOTAL_APPLIANCE': TOTAL_APPLIANCE,
                  'USED_INSTANCE': USED_INSTANCE,
                  'TOTAL_INSTANCE': TOTAL_INSTANCE,
                  'USED_STORAGE': USED_STORAGE })

        self.render("myun/index.html", **d)



class MyunInstance(LyRequestHandler):

    @authenticated
    def get(self):

        instances, page_html = self.page_view_my_instances()

        d = { 'title': _('My Instances'),
              'INSTANCE_LIST': instances, 'page_html': page_html }

        self.render( 'myun/instances.html', **d)


    def page_view_my_instances(self):

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
            instances = self.db2.query(Instance).filter(
                Instance.status.in_( slist) ).filter_by(
                user_id = self.current_user.id )
        else:
            instances = self.db2.query(Instance).filter(
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

        return instances, page_html


class InstanceManagement(LyRequestHandler):

    def get_my_instance(self, ID):
        ''' Just instance owner can get instance '''

        inst = self.db2.query(Instance).get(ID)

        if not inst:
            return None, _('No such instance: %s !') % ID

        if inst.status == DELETED_S:
            return None, _('Instance %s was deleted !') % ID

        if ( self.current_user.id != inst.user_id ):
            return None, _("No your instance !")

        return inst, ''


    def domain_delete(self, I):

        if not I.config:
            I.init_config()

        config = json.loads(I.config)
        domain = config.get('domain', {})
        if not (domain and domain.get('name')):
            return True, _('No domain needed unbinding!')

        # TODO: delete nginx binding
        from tool.domain import unbinding_domain_from_nginx
        ret, reason = unbinding_domain_from_nginx(self.db2, I.id)
        if not ret:
            return  False, _('unbinding domain error: %s') % reason

        del config['domain']
        I.config = json.dumps( config )
        self.db2.commit()

        return True, _('Success!')



class InstanceView(InstanceManagement):

    @authenticated
    def get(self, ID):

        I, msg = self.get_my_instance(ID)
        if not I:
            return self.write( msg )

        tab = self.get_argument('tab', 'general')

        JOB_LIST = self.db2.query(Job).filter(
            Job.target_id == I.id,
            Job.target_type == JOB_TARGET['INSTANCE']
            ).order_by( desc(Job.id) )
        JOB_LIST = JOB_LIST.limit(10);

        config = json.loads(I.config) if I.config else {}

        network = config.get('network', [])

        secret_form = PublicKeyForm(self)
        secret_form.key.data = config.get('public_key')

        password = config.get('passwd_hash')

        storage = config.get('storage', [])
        webssh = config.get('webssh', None)

        d = { 'I':I, 'JOB_LIST': JOB_LIST,
              'NETWORK_LIST': network,
              'secret_form': secret_form,
              'STORAGE_LIST': storage,
              'webssh': webssh,
              'TAB': tab,
              'USE_GLOBAL_PASSWD': str(I.get_config('use_global_passwd')) != 'False' }

        d['title'] = _('View instance "%s" - My Yun') % I.name

        self.render( 'myun/instance/view.html', **d)


class InstanceEdit(InstanceManagement):

    def update_dic(self, item):

        self.d['TAB'] = item

        title = None

        if item == 'general':
            title = _('Configure general info for instance')

        elif item == 'resource':
            title = _('Configure resource for instance')

        elif item == 'network':
            title = _('Configure network for instance')

        elif item == 'storage':
            title = _('Configure storage for instance')

        elif item == 'password':
            self.d['TAB'] = 'secret'
            title = _('Configure password for instance')

        elif item == 'public_key':
            self.d['TAB'] = 'secret'
            title = _('Configure public key for instance')

        elif item == 'domain':
            title = _('Configure domain for instance')

        if title:
            title += _(' - My Yun')

        self.d['title'] = title


    @authenticated
    def get(self, ID):

        I, msg = self.get_my_instance(ID)
        if not I:
            return self.write( msg )

        item = self.get_argument('item', 'general')

        self.d = {'I': I}
        self.update_dic(item)

        if item == 'general':
            self.get_general( I )
        elif item == 'resource':
            self.get_resource( I )
        elif item == 'network':
            self.get_network( I )
        elif item == 'network_clean':
            self.get_network_clean( I )
        elif item == 'storage':
            self.get_storage( I )
        elif item == 'storage_delete':
            self.get_storage_delete( I )
        elif item == 'password':
            self.get_password( I )
        elif item == 'public_key':
            self.get_public_key( I )
        elif item == 'domain':
            self.get_domain( I )
        elif item == 'domain_delete':
            self.get_domain_delete( I )
        elif item == 'webssh_toggle':
            self.get_webssh_toggle( I )
        else:
            self.write( _('Not support edit action !') )


    @authenticated
    def post(self, ID):

        I, msg = self.get_my_instance(ID)
        if not I:
            return self.write( msg )

        item = self.get_argument('item', 'general')

        self.d = {'I': I}
        self.update_dic(item)

        if item == 'general':
            self.post_general( I )
        elif item == 'resource':
            self.post_resource( I )
        elif item == 'network':
            self.post_network( I )
        elif item == 'storage':
            self.post_storage( I )
        elif item == 'password':
            self.post_password( I )
        elif item == 'public_key':
            self.post_public_key( I )
        elif item == 'domain':
            self.post_domain( I )
        else:
            self.write( _('Not support edit action !') )


    def get_general(self, I):

        form = BaseinfoForm(self)
        form.name.data = I.name
        form.summary.data = I.summary
        form.description.data = I.description

        self.d['form'] = form

        self.render( 'myun/instance/edit_general.html', **self.d)


    def post_general(self, I):

        form = BaseinfoForm(self)
        if form.validate():
            I.name = form.name.data
            I.summary = form.summary.data
            I.description = form.description.data
            I.updated = datetime.now()
            self.db2.commit()

            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=general'
            return self.redirect( url )

        self.d['form'] = form
        self.render( 'myun/instance/edit_general.html', **self.d)


    def get_resource(self, I):

        form = ResourceForm(self)
        form.cpus.data = I.cpus
        form.memory.data = I.memory

        self.d['form'] = form

        self.render( 'myun/instance/edit_resource.html', **self.d)


    def post_resource(self, I):
        form = ResourceForm(self)
        if form.validate():

            # TODO: resource limit
            RUNNING_INST_LIST = self.db2.query(Instance).filter( and_(
                    Instance.status.in_( settings.INSTANCE_SLIST_RUNING ),
                    Instance.user_id == I.user_id ) )

            USED_CPUS, USED_MEMORY = 0, 0
            for instance in RUNNING_INST_LIST:
                if instance.is_running:
                    USED_CPUS += instance.cpus
                    USED_MEMORY += instance.memory

            profile = I.user.profile
            if (form.cpus.data + USED_CPUS) > profile.cpus:
                form.cpus.errors.append( _('cpus can not greater than %s') % (profile.cpus - USED_CPUS) )
            if (form.memory.data + USED_MEMORY) > profile.memory:
                form.memory.errors.append( _('memory can not greater than %s') % (profile.memory - USED_MEMORY) )
            if not (form.cpus.errors or form.memory.errors):

                I.cpus = form.cpus.data
                I.memory = form.memory.data
                if I.is_running:
                    I.ischanged = True
                self.db2.commit()

                url = self.reverse_url('myun:instance:view', I.id)
                url += '?tab=resource'
                return self.redirect( url )


        self.d['form'] = form
        self.render( 'myun/instance/edit_resource.html', **self.d)


    def get_network_clean(self, I):

        index = self.get_argument_int('index', 1)
        nic_config = I.get_network( index )

        if nic_config:
            I.clean_network(index)
            self.db2.commit()
            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=network'
            self.redirect( url )
        else:
            self.write( _('Can not find NIC %s !') % index )


    def get_network(self, I):

        index = self.get_argument_int('index', 1)
        nic_config = I.get_network( index )

        if index == 1:
            form = NetworkForm(self)
            if nic_config:
                form.type.data = nic_config.get('type')
        else:
            if self.has_permission('network.add'):
                form = StaticNetworkForm(self)
                if nic_config:
                    form.ip.data = nic_config.get('ip')
                    form.netmask.data = nic_config.get('netmask')
                    form.gateway.data = nic_config.get('gateway')
                    form.nameservers.data = nic_config.get('nameservers')
            else:
                return self.write( _('You have not allowed to add another network !') )

        self.d['form'] = form
        self.d['INDEX'] = index
        self.render('myun/instance/edit_network.html', **self.d)


    def post_network(self, I):

        nic_total = I.get_network_count()
        ERROR = []

        index = self.get_argument_int('index', 1)
        if index == 1:
            form = NetworkForm(self)
            if form.validate():
                old_network = I.get_network()
                if form.type.data == old_network.get('type'):
                    # TODO: same configure
                    url = self.reverse_url('myun:instance:view', I.id)
                    url += '?tab=network'
                    return self.redirect( url )

                nic_type = form.type.data
                if nic_type == 'default':
                    nic_ip, nic_netmask, nic_gateway = '', '', ''

                    old_ip = old_network.get('ip', None)
                    if old_ip:
                        IPL = self.db2.query(IPPool).filter_by(
                            ip = old_ip).all()
                        for x in IPL:
                            # TODO: does this correct ?
                            if I.id == x.instance_id:
                                x.instance_id = None # unbinding
                                x.updated = datetime.now()
                                self.lytrace_ippool(x, I, release=True)
                            else:
                                logging.error("Release %s from instance %s failed, this is not it's ip" % (x.ip, I.id))

                elif nic_type == 'networkpool':
                    ok_ip = self.db2.query(IPPool).filter_by(
                        instance_id = None ).order_by(
                        asc(IPPool.id)).first()
                    if ok_ip:
                        nic_ip = ok_ip.ip
                        nic_netmask = ok_ip.network.netmask
                        nic_gateway = ok_ip.network.gateway
                        ok_ip.instance_id = I.id # binding
                        ok_ip.updated = datetime.now()
                        self.lytrace_ippool(ok_ip, I)
                    else:
                        ERROR.append( _('Can not find a useable ip from system ip pool.') )
                else:
                    ERROR.append( _('No such network type.') )
        else:
            if self.has_permission('network.add'):
                index = index if index <= nic_total + 1 else nic_total+1
                # Static network configure
                form = StaticNetworkForm(self)
                if form.validate():
                    nic_type = 'static'
                    nic_ip = form.ip.data
                    nic_netmask = form.netmask.data
                    nic_gateway = form.gateway.data
            else:
                return self.write( _('You have not allowed to add another network !') )


        self.d['INDEX'] = index
        self.d['form'] = form
        self.d['ERROR'] = ERROR
        if self.d['ERROR']:
            return self.render( 'myun/instance/edit_network.html', **self.d)

        nic_config = {
            'type': nic_type,
            'mac': I.mac, # TODO: use old mac
            'ip': nic_ip,
            'netmask': nic_netmask,
            'gateway': nic_gateway }

        # A temp hack for second network
        if index > 1:
            if index == 2:
                MAC_TEMP = '52:54:00:26:%02x:%02x'
            else:
                MAC_TEMP = '52:54:00:8%s' % (index % 10) + ':%02x:%02x'
            nic_config['mac'] = MAC_TEMP % (I.id / 256, I.id % 256)

        try:
            I.set_network( nic_config, index )
            self.db2.commit()
            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=network'
            return self.redirect( url )

        except Exception, e:
            self.d['ERROR'].append( _('save failed: %s') % e )
            self.render( 'myun/instance/edit_network.html', **self.d)


    def get_storage(self, I):

        form = StorageForm(self)
        if I.config:
            config = json.loads(I.config)
            storage = config.get('storage', [])
            if len(storage) > 0:
                storage = storage[0]
                form.type.data = storage['type']
                form.size.data = storage['size']

        self.d['form'] = form
        self.render( 'myun/instance/edit_storage.html', **self.d)


    def get_used_storage_size(self):

        from settings import INSTANCE_DELETED_STATUS as DS

        INSTANCE_LIST = self.db2.query(Instance).filter_by(
            user_id = self.current_user.id).filter(
            Instance.status != DS )

        USED = 0
        for I in INSTANCE_LIST:
            USED += I.storage

        return USED

    def post_storage(self, I):

        form = StorageForm(self)
        self.d['form'] = form

        if form.validate():
            used_storage = self.get_used_storage_size()

            if ( I.user.profile.storage
                 + I.storage # Add this instance's storage
                 - used_storage
                 ) < form.size.data:
                form.size.errors.append("Storage LIMIT: total=%s, used=%s" % ( I.user.profile.storage, used_storage ))
                return self.render( 'myun/instance/edit_storage.html', **self.d)

            storage = {
                'type': form.type.data,
                'size': form.size.data,
                }

            if I.config:
                config = json.loads(I.config)
            else:
                config = {}

            config['storage'] = [ storage ]
            I.config = json.dumps(config)

            if I.is_running:
                I.ischanged = True
            self.db2.commit()

            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=storage'
            return self.redirect( url )

        # ERROR FOUND
        self.render( 'myun/instance/edit_storage.html', **self.d)


    def get_storage_delete(self, I):

        if I.config:
            config = json.loads(I.config)
            if 'storage' in config.keys():
                del config['storage']
                I.config = json.dumps(config)
                self.db2.commit()

            if I.is_running:
                I.ischanged = True

        url = self.reverse_url('myun:instance:view', I.id)
        url += '?tab=storage'
        self.redirect( url )


    def get_password(self, I):

        form = PasswordForm(self)

        self.d['form'] = form
        self.render('myun/instance/edit_password.html', **self.d)


    def post_password(self, I):

        form = PasswordForm(self)
        if form.validate():
            # get shadow passwd
            import crypt, random, time
            salt = crypt.crypt(str(random.random()), str(time.time()))[:8]
            s = '$'.join(['','6', salt,''])
            password = crypt.crypt(form.password.data,s)

            if I.config:
                config = json.loads(I.config)
            else:
                config = {}            
            config['passwd_hash'] = password
            I.config = json.dumps(config)

            if I.is_running:
                I.ischanged = True

            I.set_config('use_global_passwd', False)

            self.db2.commit()

            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=secret'
            self.redirect( url )

        self.d['form'] = form
        self.render('myun/instance/edit_password.html', **self.d)


    def get_public_key(self, I):

        form = PublicKeyForm(self)

        if I.config:
            config = json.loads(I.config)
            if 'public_key' in config.keys():
                form.key.data = config['public_key']

        self.d['form'] = form
        self.render('myun/instance/edit_public_key.html', **self.d)


    def post_public_key(self, I):
        form = PublicKeyForm(self)
        if form.validate():
            if I.config:
                config = json.loads(I.config)
            else:
                config = {}

            config['public_key'] = form.key.data
            I.config = json.dumps(config)
            if I.is_running:
                I.ischanged = True
            self.db2.commit()

            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=secret'
            self.redirect( url )

        self.d['form'] = form
        self.render('myun/instance/edit_public_key.html', **self.d)


    def get_domain(self, I):

        self.d['ERROR'] = []

        sub, top = get_default_domain(self.db2, I.id)

        if top:
            sub = I.subdomain if I.subdomain else sub

            if not I.access_ip:
                self.d['ERROR'].append( _('Can not get access_ip, please configure instance network or run instance') )

        else:
            self.d['ERROR'].append( _('can not get domain, domain may not have been configured in Administration Console.') )

        self.d['subdomain'] = sub
        self.d['topdomain'] = top

        self.render('myun/instance/edit_domain.html', **self.d)


    def post_domain(self, I):

        d = self.d
        d['ERROR'] = []

        sub, d['topdomain'] = get_default_domain(self.db2, I.id)

        if d['topdomain']:
            oldsub = I.subdomain if I.subdomain else sub

        subdomain = self.get_argument('subdomain', None)
        if not subdomain:
            d['ERROR'].append( _('Domain is not configured!') )

        if subdomain != oldsub:
            d['subdomain'] = subdomain
            if subdomain.isalpha():
                exist_domain = self.db2.query(Instance.id).filter_by(
                    subdomain = subdomain ).first()
                if exist_domain:
                    d['ERROR'].append( _('Domain name is taken!') )
                if len(subdomain) > 16:
                    d['ERROR'].append( _("Domain name is too long.") )
            else:
                d['ERROR'].append( _('Please use alpha characters in domain name!') )

        if d['ERROR']:
            return self.render('myun/instance/edit_domain.html', **d)

        # Updated instance subdomain value
        I.subdomain = subdomain
        self.db2.commit()

        fulldomain = '.'.join([subdomain, d['topdomain']])

        # Binding in nginx
        from tool.domain import binding_domain_in_nginx
        ret, reason = binding_domain_in_nginx(
            self.db2, I.id, domain = fulldomain )
        if not ret:
            d['ERROR'].append(_('binding domain error: %s') % reason )

        if not I.config:
            I.init_config()

        config = json.loads(I.config)
            
        if 'domain' in config.keys():
            domain = config['domain']
        else:
            domain = {}

        domain['name'] = fulldomain
        domain['ip'] = I.access_ip
        config['domain'] = domain

        I.config = json.dumps( config )

        I.updated = datetime.now()
        if I.is_running:
            I.ischanged = True
        self.db2.commit()

        if d['ERROR']:
            self.render('myun/instance/edit_domain.html', **d)
        else:
            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=domain'
            self.redirect( url )

    def get_domain_delete(self, I):

        ret, reason = self.domain_delete( I )
        if ret:
            I.subdomain = None
            self.db2.commit()
            url = self.reverse_url('myun:instance:view', I.id)
            url += '?tab=domain'
            self.redirect( url )
        else:
            self.write( _('Delete domain failed: %s') % reason )


    def get_webssh_toggle(self, I):

        if not I.config:
            I.init_config()

        config = json.loads(I.config)
            
        if 'webssh' in config.keys():
            webssh = config['webssh']
        else:
            webssh = {}

        if webssh.get('status') != 'enable':
            webssh['status'] = 'enable'
            webssh['port'] = 8001
            config['webssh'] = webssh
        else:
            if 'webssh' in config.keys():
                del config['webssh']

        I.config = json.dumps( config )
        if I.is_running:
            I.ischanged = True
        self.db2.commit()
        # no news is good news



class MyunAppliance(LyRequestHandler):

    @authenticated
    def get(self):

        apps, page_html = self.page_view_my_appliances()

        d = { 'title': _('My Appliances'),
              'APPLIANCE_LIST': apps, 'page_html': page_html }

        self.render( 'myun/appliances.html', **d)


    def page_view_my_appliances(self):

        #catalog_id = self.get_argument_int('c', 1)
        page_size = self.get_argument_int('sepa', 10)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        apps = self.db2.query(Appliance).filter_by(
            user_id=self.current_user.id).order_by(by_exp)

        total = apps.count()
        apps = apps.slice(start, stop)
            
        page_html = pagination(self.request.uri, total, page_size, cur_page)

        return apps, page_html
