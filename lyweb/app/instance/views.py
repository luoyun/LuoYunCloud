# coding: utf-8

import logging, struct, socket, re, os, json, time
from datetime import datetime

from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous
import tornado

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_

from app.appliance.models import Appliance
from app.instance.models import Instance
from app.job.models import Job
from app.system.models import IpAssign, LuoYunConfig

from app.instance.forms import CreateInstanceBaseForm, \
    CreateInstanceForm, BaseinfoForm, ResourceForm, \
    NetworkForm, StorageForm, PasswordForm, PublicKeyForm

from lycustom import has_permission

import settings
from settings import INSTANCE_DELETED_STATUS as DELETED_S
from settings import JOB_ACTION, JOB_TARGET

from lycustom import LyRequestHandler, Pagination



IMAGE_SUPPORT=True
try:
    import Image
except ImportError:
    IMAGE_SUPPORT=False


class InstRequestHandler(LyRequestHandler):

    def create_logo2(self, app, inst_id):
        ''' Create logo '''

        if not hasattr(app, 'logoname'):
            return False

        if not app.logoname:
            return False

        applogo = os.path.join(
            self.settings['appliance_top_dir'],
            app.logoname )

        if not os.path.exists(applogo):
            logging.error('%s not exist' % applogo)
            return False

        if not IMAGE_SUPPORT:
            return applogo

        wm = os.path.join(
            self.settings['static_path'],
            'image/watermark.png' )

        if not os.path.exists(wm):
            logging.error('%s not exist' % wm)
            return False

        spath = os.path.join(
            self.settings['static_path'], 'instance_logo' )
        if not os.path.exists(spath):
            logging.error('%s not exist' % spath)

        from yimage import watermark

        I = Image.open(applogo)

        M = Image.open(wm)

        sname = 'ilogo_%s.%s' % (
            inst_id, applogo.split('.')[-1] )

        fullpath = os.path.join( spath, sname )

        position = ( (I.size[0] - M.size[0]) / 2,
                     I.size[1] - M.size[1] )
        img = watermark(I, M, position, 0.3)
        img.save( fullpath )

        return sname


    def done(self, msg):

        ajax = self.get_argument_int('ajax', 0)

        if ajax:
            self.write(msg)
        else:
            self.render( 'instance/action_result.html',
                         msg = msg )


    # get_instance(), make sure user can access instance
    def get_instance(self, id, isowner=False):

        inst = self.db2.query(Instance).get(id)

        if not inst:
            self.done( _('No such instance: %s !') % id )
            return None

        if inst.isprivate:
            if ( (not self.current_user) or (
                    (self.current_user.id != inst.user_id) and
                    (not self.has_permission('admin')) )
                 ):
                self.done( _('Instance %s is private !') % id )
                return None

        if inst.status == DELETED_S:
            self.done( _('Instance %s is deleted !') % id )
            return None

        # Just user can do
        if isowner:
            if inst.user_id != self.current_user.id:
                self.done( _('Only owner can do this!') )
                return None

        return inst


    def get_my_instance(self, ID, allow_admin=False):
        ''' Just instance owner or admin can get instance '''

        inst = self.db2.query(Instance).get(ID)

        if not inst:
            return None, _('No such instance: %s !') % ID

        if inst.status == DELETED_S:
            return None, _('Instance %s is deleted !') % ID

        if ( (not self.current_user) or (self.current_user.id != inst.user_id) ):
            if not (allow_admin and self.has_permission('admin')):
                return None, _('Instance %s is private !') % ID

        return inst, ''


    def run_job(self, I, action_id):

        if I.lastjob and (not I.lastjob.completed):
            if not ( action_id == JOB_ACTION['STOP_INSTANCE'] and
                 I.lastjob.canstop ):
                # TODO: status = 100, timeout > 60s
                return _("Previous task is not finished !")

        # Create new job
        job = Job( user = self.current_user,
                   target_type = JOB_TARGET['INSTANCE'],
                   target_id = I.id,
                   action = action_id )

        self.db2.add(job)
        self.db2.commit()
        
        I.lastjob = job

        try:
            self._job_notify( job.id )
        except Exception, e:
            #[Errno 113] No route to host
            # TODO: should be a config value
            job.status = settings.JOB_S_FAILED
            return _("Connect to control server failed: %s") % e

        self.db2.commit()
        return _('Task starts successfully.')


    def update_ipassign(self, ip, instance):
        ''' Update IpAssign table '''

        ipassign = self.db2.query(IpAssign).filter_by(ip=ip).first()
        if ipassign:
            ipassign.user_id = self.current_user.id
            ipassign.instance_id = instance.id
            updated = datetime.now()
        else:
            c = IpAssign( ip = ip,
                          user = self.current_user,
                          instance = instance )
            self.db2.add( c )

        self.db2.commit()


    def domain_delete(self, inst):

        if not inst.config:
            inst.init_config()

        config = json.loads(inst.config)
        domain = config.get('domain', {})
        if not (domain and domain.get('name')):
            return True, _('No domain needed unbinding!')

        # TODO: delete nginx binding
        from tool.domain import unbinding_domain_from_nginx
        ret, reason = unbinding_domain_from_nginx(self.db2, inst.id)
        if not ret:
            return  False, _('unbinding domain error: %s') % reason

        del config['domain']
        inst.config = json.dumps( config )
        self.db2.commit()

        return True, _('Success!')


    def get_domain(self, I): # I is a instance obj

        domain = self.db2.query(LuoYunConfig).filter_by(key='domain').first()

        if not domain: return ''

        domain =  json.loads(domain.value)
        topdomain = domain['topdomain'].strip('.')

        if I.subdomain:
            subdomain = I.subdomain
        else:
            prefix = domain['prefix']
            suffix = domain['suffix']
            subdomain = '%s%s%s' % (prefix, I.id, suffix)

        return '.'.join([subdomain, topdomain])

    def get_domain2(self, I):
        L = self.get_domain(I).split('.')
        return (L[0], '.'.join(L[1:])) if L else (None, None)



class Index(InstRequestHandler):
    ''' Index home '''

    def initialize(self, title = _('LuoYun Public Instance')):
        self.title = title


    def get(self):

        # TODO: a temp hack for status sync
        self.db2.commit()

        # TODO:
        #self.set_secure_cookie('session_key', session_key)
        instance_sort = self.get_secure_cookie('instance_sort')
        instance_sort = '?view=all'

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'updated')
        sort = self.get_argument('sort', 'desc')
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
            slist = settings.INSTANCE_SLIST_ALL

        instances = self.db2.query(Instance).filter(
            Instance.isprivate != True ).filter(
            Instance.status.in_( slist) )

        if view == 'self' and self.current_user:
            instances = instances.filter_by(
                user_id = self.current_user.id )

        #by_obj = Instance.created if by == 'created' else Instance.updated
        if by == 'created':
            by_obj = Instance.created
        # TODO: sorted by username
        #elif by == 'username':
        #    by_obj = Instance.user.username
        else:
            by_obj = Instance.updated

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

        d = { 'title': self.title,
              'INSTANCE_LIST': instances,
              'cur_page': cur_page,
              'page_html': page_html }

        # TODO: save user sort method
        self.set_secure_cookie('instance_sort', instance_sort)

        self.render("instance/index.html", **d)



class View(InstRequestHandler):
    ''' Show Instance's information '''

    #@authenticated
    def get(self, id):

        # TODO: a temp hack for status sync
        self.db2.commit()

        self.inst = self.get_instance(id)
        if not self.inst: return

        obj = self.get_argument('view', 'baseinfo')
        if obj == 'network':
            self.get_network()
        elif obj == 'resource':
            self.get_resource()
        elif obj == 'storage':
            self.get_storage()
        elif obj == 'secret':
            self.get_secret()
        elif obj == 'delete':
            self.get_delete()
        elif obj == 'joblist':
            self.get_joblist()
        elif obj == 'domain':
            self.get_domain()
        elif obj == 'webssh':
            self.get_webssh()
        else:
            # other obj is baseinfo
            self.get_baseinfo()


    def get_baseinfo(self):

        d = { 'title': _('Baseinfo of instance %s') % self.inst.id,
              'instance': self.inst,
              'JOB_RESULT': self.get_argument('job_result', None)}

        self.render('instance/baseinfo.html', **d)



    def get_resource(self):
        d = { 'title': _('Resource of instance %s') % self.inst.id,
              'instance': self.inst }
        self.render('instance/resource.html', **d)


    def get_network(self):

        inst = self.inst
        network = []

        if inst.config:
            config = json.loads(inst.config)
            if 'network' in config.keys():
                network = config['network']

        d = { 'title': _('Network configuration of instance %s') % self.inst.id,
              'instance': inst, 'NETWORK_LIST': network }

        self.render('instance/network.html', **d)


    def get_storage(self):

        inst = self.inst
        storage = []

        if inst.config:
            config = json.loads(inst.config)
            if 'storage' in config.keys():
                storage = config['storage']

        d = { 'title': _('Storage configuration of instance %s') % self.inst.id,
              'instance': inst, 'STORAGE_LIST': storage }

        self.render('instance/storage.html', **d)


    def get_secret(self):

        inst = self.inst
        password = ''
        publickey = ''

        form = PublicKeyForm()

        if inst.config:
            config = json.loads(inst.config)
            if 'passwd_hash' in config.keys():
                password = config['passwd_hash']
            if 'public_key' in config.keys():
                form.key.data = config['public_key']

        d = { 'title': _('Configure Password'),
              'instance': inst, 'password': password,
              'form': form,
              'saved': self.get_argument('saved', None) }

        self.render('instance/secret.html', **d)



    def get_delete(self):

        d = { 'title': _('Delete Instance'),
              'instance': self.inst }

        self.render('instance/delete.html', **d)


    def get_joblist(self):

        JOB_LIST = self.db2.query(Job).filter(
            Job.target_id == self.inst.id,
            Job.target_type == JOB_TARGET['INSTANCE']
            ).order_by( desc(Job.id) )
        JOB_LIST = JOB_LIST.limit(10);

        d = { 'title': _('Job History'),
              'instance': self.inst,
              'JOB_LIST': JOB_LIST }

        self.render('instance/joblist.html', **d)


    def get_domain(self):
        d = { 'title': _('Domain Binding'),
              'instance': self.inst }

        self.render('instance/domain.html', **d)


    def get_webssh(self):
        if not self.inst.config:
            self.inst.init_config()

        config = json.loads(self.inst.config)
        if 'webssh' in config.keys():
            webssh = config['webssh']
        else:
            webssh = None

        d = { 'title': _('Configure WebSSH'),
              'instance': self.inst, 'webssh': webssh }

        self.render('instance/webssh.html', **d)



class Delete(InstRequestHandler):

    @authenticated
    def get(self, id):

        I = self.db2.query(Instance).get(id)
        d = {'I': I, 'E': []}

        if I:
            # TODO: no running delete !
            if I.is_running:
                d['E'].append( _("Can not delete a running instance!") )

            # TODO: delete domain binding
            ret, reason = self.domain_delete( I )
            if not ret:
                d['E'].append( reason )

        else:
            d['E'].append( _('No instance %s!') % id )


        if d['E']:
            return self.render('instance/delete_return.html', **d)

        I.status = DELETED_S
        I.subdomain = '_notexist_%s_' % I.id
        self.db2.commit()

        ipassign_list = self.db2.query(IpAssign).filter_by(
            instance_id = I.id ).all()
        for ipassign in ipassign_list:
            self.db2.delete( ipassign )
            self.db2.commit()

        # delete instance files
        d['MSG'] = self.run_job(I, JOB_ACTION['DESTROY_INSTANCE'])
        return self.render('instance/delete_return.html', **d)



class InstanceControl(InstRequestHandler):
    ''' stop/run/reboot/query '''

    #@authenticated
    def get(self, ID):

        # Important !!! IE use cache !
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        if not self.current_user:
            return self.write( {
                    'return_code': 1,
                    'msg': _('You have not login !') } )

        inst, msg = self.get_my_instance(ID, allow_admin=True)
        if not inst:
            return self.write( {'return_code': 1, 'msg': msg } )

        action = self.get_argument('action', '').lower()

        ret = 0
        if action == 'run':
            msg = self.run( inst )
        elif action == 'stop':
            msg = self.stop( inst )
        elif action == 'reboot':
            msg = self.reboot( inst )
        elif action == 'query':
            msg = self.query( inst )
        else:
            msg = _('Just support run/stop/reboot/query action')
            ret = 1

        inst.updated = datetime.now()
        if inst.ischanged:
            inst.ischanged = False
        self.db2.commit()

        self.write( {'return_code': ret, 'msg': msg } )
                     

    def reboot(self, instance):
        return self.run_job(instance, JOB_ACTION['REBOOT_INSTANCE'])


    def query(self, instance):
        if instance.need_query:
            return self.run_job(instance, JOB_ACTION['QUERY_INSTANCE'])
        else:
            return _('Instance does not need query.')


    def stop(self, instance):
        
        if instance.is_running:
            return self.run_job(instance, JOB_ACTION['STOP_INSTANCE'])
        else:
            return _('Instance is stopped now !')

    def run(self, instance):

        ret = self.have_resource(instance)
        if ret: return ret

        if instance.is_running:
            return _('Instance is running now !')

        # TODO: a temp hack
        self.set_nameservers(instance)
        self.rebinding_domain(instance)

        return self.run_job(instance, JOB_ACTION['RUN_INSTANCE'])

    def have_resource(self, inst):

        # TODO: owner or myself ?
        #owner = self.current_user
        owner = inst.user

        USED_INSTANCES = self.db2.query(Instance).filter(
            Instance.user_id == owner.id).all()
        USED_CPUS = 0
        USED_MEMORY = 0
        for I in USED_INSTANCES:
            if I.is_running:
                USED_CPUS += I.cpus
                USED_MEMORY += I.memory

        TOTAL_CPU = owner.profile.cpus - USED_CPUS
        TOTAL_MEM = owner.profile.memory - USED_MEMORY

        desc = ''
        if TOTAL_CPU < inst.cpus:
            if TOTAL_CPU < 0: TOTAL_CPU = 0
            desc = _('need %s CPU, but %s have.') % (inst.cpus, TOTAL_CPU)
        if TOTAL_MEM < inst.memory:
            if TOTAL_MEM < 0: TOTAL_MEM = 0
            desc = _('need %sMB memory, but %sMB have.') % (inst.memory, TOTAL_MEM)
        if desc:
            return _('No resource: %s') % desc


    def set_nameservers(self, instance):
        ''' TODO: This is a temp hack '''

        NS = self.db2.query(LuoYunConfig).filter_by(
            key='nameservers').first()

        if NS and instance.config:
            config = json.loads(instance.config)
            config['nameservers'] = NS.value
            instance.config = json.dumps(config)
            self.db2.commit()
                

    # TODO: rebinding domain
    def rebinding_domain(self, instance):
        # Binding in nginx
        from tool.domain import binding_domain_in_nginx
        ret, reason = binding_domain_in_nginx(
            self.db2, instance.id, domain = self.get_domain(instance) )
        if not ret:
            logging.warning(_('binding domain error: %s') % reason)
        # TODO: update config about domain
        self.binding_domain(instance)

    def binding_domain(self, instance):

        full_domain = self.get_domain( instance )

        if not instance.config:
            instance.init_config()

        config = json.loads(instance.config)
            
        if 'domain' in config.keys():
            domain = config['domain']
        else:
            domain = {}

        domain['name'] = full_domain
        domain['ip'] = instance.access_ip
        config['domain'] = domain

        instance.config = json.dumps( config )
        instance.updated = datetime.now()
        self.db2.commit()


class CreateInstance(InstRequestHandler):

    @has_permission('instance.create')
    def prepare(self):

        _id = self.get_argument('appliance_id', 0)
        self.appliance = self.db2.query(Appliance).get(_id)

        if ( self.appliance and self.appliance.isprivate and
             self.current_user.id != self.appliance.user_id ):
            self.write( _('Appliance is private: %s') % _id )
            return self.finish()

        if self.appliance and not self.appliance.isuseable:
            self.write( _('Appliance is locked: %s') % _id )
            return self.finish()

        # Have resources ?
        USED_INSTANCES = self.db2.query(Instance.id).filter(
            Instance.user_id == self.current_user.id ).count()

        RUNNING_INST_LIST = self.db2.query(Instance).filter( and_(
            Instance.status.in_( settings.INSTANCE_SLIST_RUNING ),
            Instance.user_id == self.current_user.id ) )
        USED_CPUS, USED_MEMORY = 0, 0
        for I in RUNNING_INST_LIST:
            if I.is_running:
                USED_CPUS += I.cpus
                USED_MEMORY += I.memory

        profile = self.current_user.profile
        if ( (USED_INSTANCES >= profile.instances) or 
             (USED_CPUS >= profile.cpus) or
             (USED_MEMORY >= profile.memory) ):
            url = self.get_no_resource_url() + "?reason=Resource Limit"
            self.redirect( url )
            return self.finish()

        self.USED_CPUS = USED_CPUS
        self.USED_MEMORY = USED_MEMORY
        self.d = { 'title': _('Create Instance'),
                   'USED_CPUS': USED_CPUS,
                   'USED_MEMORY': USED_MEMORY }


    def get(self):
 
        if not self.appliance:
            form = CreateInstanceForm()
            apps = self.db2.query(Appliance).filter_by(
                isprivate = False).filter_by(
                isuseable = True)
            if not apps.count():
                return self.write( _("No appliance found, please upload appliance first!") )
            form.appliance.query = apps.all()
        else:
            form = CreateInstanceBaseForm()
            form.name.data = self.appliance.name

        self.d['APPLIANCE'] = self.appliance
        self.d['form'] = form
        self.render( 'instance/create.html', **self.d )


    def post(self):

        if  self.appliance:
            form = CreateInstanceBaseForm( self.request.arguments )
            app = self.appliance 
        else:
            form = CreateInstanceForm( self.request.arguments )
            form.appliance.query = self.db2.query(Appliance).filter_by(
                isprivate = False).filter_by(isuseable = True).all()
            app = form.appliance.data

        self.d['APPLIANCE'] = app
        self.d['form'] = form

        if form.validate():
            # instance name have used by myself ?
            exist_inst = self.db2.query(Instance).filter_by(
                name = form.name.data).filter_by(
                user_id = self.current_user.id).first()
            if exist_inst:
                form.name.errors.append( _('You have used the name for a instance !') )

            # TODO: resource limit
            profile = self.current_user.profile
            if (form.cpus.data + self.USED_CPUS) > profile.cpus:
                form.cpus.errors.append( _('cpus can not greater than %s') % (profile.cpus - self.USED_CPUS) )
            if (form.memory.data + self.USED_MEMORY) > profile.memory:
                form.memory.errors.append( _('memory can not greater than %s') % (profile.memory - self.USED_MEMORY) )

            if ( form.name.errors or form.cpus.errors
                 or form.memory.errors ):
                return self.render( 'instance/create.html', **self.d )

            # Create new instance
            instance = Instance(
                name=form.name.data, user=self.current_user, appliance=app )

            instance.cpus = form.cpus.data
            instance.memory = form.memory.data
            instance.isprivate = form.isprivate.data

            self.db2.add(instance)
            self.db2.commit()

            instance.mac = '92:1B:40:26:%02x:%02x' % (
                instance.id / 256, instance.id % 256 )
            self.db2.commit()

#            instance.logo = self.create_logo(app, instance.id)
            instance.save_logo()

            # TODO
            self.set_ip( instance )
            self.binding_domain( instance )

            url = self.reverse_url('instance:view', instance.id)
            return self.redirect(url)

        # Something is wrong
        self.render( 'instance/create.html', **self.d )


    def set_ip(self, instance):

        # TODO: ip assign should have a global switch flag
        NPOOL = []
        TOTAL_POOL = settings.NETWORK_POOL[0]

        if not TOTAL_POOL: return

        the_good_ip = None
        for ip in TOTAL_POOL['pool']:
            if not self.db2.query(IpAssign).filter_by( ip = ip ).first():
                the_good_ip = ip
                break

        if not the_good_ip: return

        network = {
            'type': 'default',
            'mac': instance.mac, # TODO: use old mac
            'ip': the_good_ip,
            'netmask': TOTAL_POOL['netmask'],
            'gateway': TOTAL_POOL['gateway']
            }

        config = json.loads(instance.config) if instance.config else {}
        config['network'] = [network]

        instance.config = json.dumps(config)
        self.db2.commit()

        self.update_ipassign( ip, instance )


    def binding_domain(self, instance):

        # Updated instance subdomain value
        sub, top= self.get_domain2( instance )
        if sub and top:
            instance.subdomain = sub
            self.db2.commit()
        else:
            return None

        full_domain = self.get_domain( instance )
        # Binding in nginx
        from tool.domain import binding_domain_in_nginx
        ret, reason = binding_domain_in_nginx(
            self.db2, instance.id, domain = full_domain )
        if not ret:
            return None

        if not instance.config:
            instance.init_config()

        config = json.loads(instance.config)
            
        if 'domain' in config.keys():
            domain = config['domain']
        else:
            domain = {}

        domain['name'] = full_domain
        domain['ip'] = instance.access_ip
        config['domain'] = domain

        instance.config = json.dumps( config )
        instance.updated = datetime.now()
        self.db2.commit()



class BaseinfoEdit(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = BaseinfoForm()
        form.name.data = inst.name
        form.summary.data = inst.summary
        form.description.data = inst.description


        d = { 'title': _('Edit Baseinfo'),
              'instance': inst, 'form': form }

        self.render('instance/baseinfo_edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = BaseinfoForm( self.request.arguments )
        if form.validate():
            inst.name = form.name.data
            inst.summary = form.summary.data
            inst.description = form.description.data
            inst.updated = datetime.now()
            self.db2.commit()

            url = self.reverse_url('instance:view', id)
            url += '?view=baseinfo'
            return self.redirect( url )

        # Get error
        d = { 'title': _('Edit Baseinfo'),
              'instance': inst, 'form': form }
        self.render('instance/baseinfo_edit.html', **d)



class ResourceEdit(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = ResourceForm()
        form.cpus.data = inst.cpus
        form.memory.data = inst.memory

        d = { 'title': _('Edit Resource'),
              'instance': inst, 'form': form }

        self.render('instance/resource_edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = ResourceForm( self.request.arguments )
        if form.validate():

            # TODO: resource limit
            RUNNING_INST_LIST = self.db2.query(Instance).filter( and_(
                    Instance.status.in_( settings.INSTANCE_SLIST_RUNING ),
                    Instance.user_id == inst.user_id ) )

            USED_CPUS, USED_MEMORY = 0, 0
            for I in RUNNING_INST_LIST:
                if I.is_running:
                    USED_CPUS += I.cpus
                    USED_MEMORY += I.memory

            profile = inst.user.profile
            if (form.cpus.data + USED_CPUS) > profile.cpus:
                form.cpus.errors.append( _('cpus can not greater than %s') % (profile.cpus - USED_CPUS) )
            if (form.memory.data + USED_MEMORY) > profile.memory:
                form.memory.errors.append( _('memory can not greater than %s') % (profile.memory - USED_MEMORY) )
            if form.cpus.errors or form.memory.errors:
                d = { 'title': _('Edit Resource'),
                      'instance': inst, 'form': form }
                self.render('instance/resource_edit.html', **d)
                

            inst.cpus = form.cpus.data
            inst.memory = form.memory.data
            if inst.is_running:
                inst.ischanged = True
            self.db2.commit()

            url = self.reverse_url('instance:view', id)
            url += '?view=resource'
            return self.redirect( url )

        # Get error
        d = { 'title': _('Edit Resource'),
              'instance': inst, 'form': form }
        self.render('instance/resource_edit.html', **d)



class NetworkEdit(InstRequestHandler):

    def update_form(self, form):
        NPOOL = []
        TOTAL_POOL = settings.NETWORK_POOL[0]

        if not TOTAL_POOL:
            form.ip.choices = []
            return

        for ip in TOTAL_POOL['pool']:
            if not self.db2.query(IpAssign).filter_by( ip = ip ).first():
                NPOOL.append( (ip, ip) )

        form.ip.choices = NPOOL
        form.netmask.data = TOTAL_POOL['netmask']
        form.gateway.data = TOTAL_POOL['gateway']

    @authenticated
    def get(self, id):
        # if not inst.config.network, just add

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = NetworkForm()
        self.update_form( form )

        if inst.config:
            config = json.loads(inst.config)
            if 'network' in config.keys():
                network = config['network']
                if len(network) > 0:
                    network = network[0]
                    form.type.data = network['type']
                    form.ip.data = network['ip']
                    form.netmask.data = network['netmask']
                    form.gateway.data = network['gateway']


        d = { 'title': _('Edit Network'),
              'instance': inst, 'form': form }

        self.render('instance/network_edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = NetworkForm( self.request.arguments )
        self.update_form( form )

        if form.validate():

            network = {
                'type': form.type.data,
                'mac': inst.mac, # TODO: use old mac
                'ip': form.ip.data,
                'netmask': form.netmask.data,
                'gateway': form.gateway.data
                }

            if inst.config:
                config = json.loads(inst.config)
            else:
                config = {}

            config['network'] = [network]
            inst.config = json.dumps(config)
            #print 'config = ', inst.config
            self.db2.commit()

            # Update IpAssign table
            ipassign = self.db2.query(IpAssign).filter_by( ip = network['ip'] ).first()
            if ipassign:
                ipassign.user_id = self.current_user.id
                ipassign.instance_id = id
                updated = datetime.now()
            else:
                c = IpAssign( ip = network['ip'],
                              user = self.current_user,
                              instance = inst )
                self.db2.add( c )

            if inst.is_running:
                inst.ischanged = True
            self.db2.commit()

            url = self.reverse_url('instance:view', id)
            url += '?view=network'
            return self.redirect( url )

        # Get error
        d = { 'title': _('Edit Network'),
              'instance': inst, 'form': form }
        self.render('instance/network_edit.html', **d)



class NetworkDelete(InstRequestHandler):

    @authenticated
    def get(self, id):
        # delete inst.config.network

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        if inst.config:
            config = json.loads(inst.config)
            if 'network' in config.keys():
                ip = config['network'][0]['ip']
                del config['network']
                inst.config = json.dumps(config)

                # delete ip from IpAssign
                ipassign = self.db2.query(IpAssign).filter_by( ip = ip ).first()
                self.db2.delete( ipassign )
                self.db2.commit()

            if inst.is_running:
                inst.ischanged = True

        url = self.reverse_url('instance:view', id)
        url += '?view=network'
        return self.redirect( url )


class StorageEdit(InstRequestHandler):

    @authenticated
    def get(self, id):
        # if not inst.config.storage, just add

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = StorageForm()
        if inst.config:
            config = json.loads(inst.config)
            if 'storage' in config.keys():
                storage = config['storage']
                if len(storage) > 0:
                    storage = storage[0]
                    form.type.data = storage['type']
                    form.size.data = storage['size']

        d = { 'title': _('Edit Storage'),
              'instance': inst, 'form': form }

        self.render('instance/storage_edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = StorageForm( self.request.arguments )
        if form.validate():

            # Is there have storage resource ?
            used_storage = self.get_used_storage_size()
#            print '''inst.user.profile.storage = %s,
#used_storage = %s,
#inst.storage = %s''' % (inst.user.profile.storage,
#                        used_storage, inst.storage)
            if ( inst.user.profile.storage
                 + inst.storage # Add this instance's storage
                 - used_storage
                 ) < form.size.data:
                url = self.get_no_resource_url()
                url += "?reason=Storage LIMIT&total=%s&used=%s" % ( inst.user.profile.storage, used_storage )
                return self.redirect( url )

            storage = {
                'type': form.type.data,
                'size': form.size.data,
                }

            if inst.config:
                config = json.loads(inst.config)
            else:
                config = {}

            config['storage'] = [ storage ]
            inst.config = json.dumps(config)

            if inst.is_running:
                inst.ischanged = True
            self.db2.commit()

            url = self.reverse_url('instance:view', id)
            url += '?view=storage'
            return self.redirect( url )

        # Get error
        d = { 'title': _('Edit Storage'),
              'instance': inst, 'form': form }
        self.render('instance/storage_edit.html', **d)


    def get_used_storage_size(self):

        from settings import INSTANCE_DELETED_STATUS as DS

        INSTANCE_LIST = self.db2.query(Instance).filter_by(
            user_id = self.current_user.id).filter(
            Instance.status != DS )

        USED = 0
        for I in INSTANCE_LIST:
            USED += I.storage

        return USED



class StorageDelete(InstRequestHandler):

    @authenticated
    def get(self, id):
        # delete inst.config.storage

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        if inst.config:
            config = json.loads(inst.config)
            if 'storage' in config.keys():
                del config['storage']
                inst.config = json.dumps(config)
                self.db2.commit()

            if inst.is_running:
                inst.ischanged = True

        url = self.reverse_url('instance:view', id)
        url += '?view=storage'
        return self.redirect( url )



class PasswordEdit(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = PasswordForm()

        d = { 'title': _('Edit Root Password for Instance'),
              'instance': inst, 'form': form }

        self.render('instance/password_edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = PasswordForm( self.request.arguments )
        if form.validate():
            # get shadow passwd
            import crypt, random, time
            salt = crypt.crypt(str(random.random()), str(time.time()))[:8]
            s = '$'.join(['','6', salt,''])
            password = crypt.crypt(form.password.data,s)
            if inst.config:
                config = json.loads(inst.config)
            else:
                config = {}            
            config['passwd_hash'] = password
            inst.config = json.dumps(config)

            if inst.is_running:
                inst.ischanged = True
            self.db2.commit()

            url = self.reverse_url('instance:view', id)
            url += '?view=secret'
            return self.redirect( url )

        # Get error
        d = { 'title': _('Edit Root Password for Instance'),
              'instance': inst, 'form': form }
        self.render('instance/password_edit.html', **d)



class PublicKeyEdit(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = PublicKeyForm()
        if inst.config:
            config = json.loads(inst.config)
            if 'public_key' in config.keys():
                form.key.data = config['public_key']

        d = { 'title': _('Edit SSH Public Key'),
              'instance': inst, 'form': form }

        self.render('instance/publickey_edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        form = PublicKeyForm( self.request.arguments )
        if form.validate():
            if inst.config:
                config = json.loads(inst.config)
            else:
                config = {}

            config['public_key'] = form.key.data
            inst.config = json.dumps(config)
            if inst.is_running:
                inst.ischanged = True
            self.db2.commit()

            url = self.reverse_url('instance:view', id)
            url += '?view=secret&saved=True'
            return self.redirect( url )

        # Get error
        d = { 'title': _('Edit SSH Public Key'),
              'instance': inst, 'form': form }
        self.render('instance/publickey_edit.html', **d)



class DomainEdit(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        d = { 'title': _('Configure Domain'),
              'instance': inst, 'ERROR': [] }

        d['subdomain'], d['topdomain'] = self.get_domain2( inst )
        if not d['subdomain']:
            d['ERROR'].append( _('can not get domain, domain may not have been configured in Administration Console.') )

        if not inst.access_ip:
            d['ERROR'].append( _('Can not get access_ip, please configure instance network or run instance') )

        self.render('instance/domain_edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        d = { 'title': _('Configure Domain'),
              'instance': inst, 'ERROR': [] }

        oldsub, d['topdomain'] = self.get_domain2( inst )

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
            return self.render('instance/domain_edit.html', **d)

        # Updated instance subdomain value
        inst.subdomain = subdomain
        self.db2.commit()

        # Binding in nginx
        from tool.domain import binding_domain_in_nginx
        ret, reason = binding_domain_in_nginx(
            self.db2, inst.id, domain = self.get_domain(inst) )
        if not ret:
            d['ERROR'] = _('binding domain error: %s') % reason

        if not inst.config:
            inst.init_config()

        config = json.loads(inst.config)
            
        if 'domain' in config.keys():
            domain = config['domain']
        else:
            domain = {}

        domain['name'] = self.get_domain( inst )
        domain['ip'] = inst.access_ip
        config['domain'] = domain

        inst.config = json.dumps( config )

        inst.updated = datetime.now()
        if inst.is_running:
            inst.ischanged = True
        self.db2.commit()

        url = self.reverse_url('instance:view', inst.id)
        url += '?view=domain'
        return self.redirect(url)



class DomainDelete(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        ret, reason = self.domain_delete( inst )
        if not ret:
            return self.done( reason )

        url = self.reverse_url('instance:view', inst.id)
        url += '?view=domain'
        return self.redirect(url)



class WebSSHEnable(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        if not inst.config:
            inst.init_config()

        config = json.loads(inst.config)
            
        if 'webssh' in config.keys():
            webssh = config['webssh']
        else:
            webssh = {}

        webssh['status'] = 'enable'
        webssh['port'] = 8001

        config['webssh'] = webssh

        inst.config = json.dumps( config )
        if inst.is_running:
            inst.ischanged = True
        self.db2.commit()

        url = self.reverse_url('instance:view', inst.id)
        url += '?view=webssh'
        return self.redirect(url)



class WebSSHDisable(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.get_instance(id, isowner=True)
        if not inst: return

        if not inst.config:
            inst.init_config()

        config = json.loads(inst.config)
        if 'webssh' in config.keys():
            del config['webssh']

        inst.config = json.dumps( config )
        if inst.is_running:
            inst.ischanged = True
        self.db2.commit()

        url = self.reverse_url('instance:view', inst.id)
        url += '?view=webssh'
        return self.redirect(url)


class SetPrivate(InstRequestHandler):

    @authenticated
    def get(self, id):

        # TODO:
        url = self.get_argument('next_url', None)
        if not url:
            url = self.reverse_url('instance:view', id)

        inst = self.db2.query(Instance).get(id)
        if not inst:
            return self.write( _('No such instance!') )

        if not ( inst.user_id == self.current_user.id or
                 self.has_permission('admin') ):
            return self.write( _('No permission!') )

        flag = self.get_argument('flag', None)
        inst.isprivate = True if flag == 'true' else False
        self.db2.commit()

        self.redirect( url )



class Status(InstRequestHandler):

    ''' return all status of instance by json data '''

    @asynchronous
    def get(self, ID):

        inst = self.db2.query(Instance).get(ID)
        if not inst:
            self.write( _('No such instance!') )
            return self.finish()

        status = { 'job': self.get_argument_int('job_status', 0),
                   'instance': self.get_argument_int('instance_status', 0) }

        self.check_status(inst, status)


    def check_status(self, instance, status):

        job = instance.lastjob

        # TODO: a temp hack for old job action
        if not job:
            old = self.db2.query(Job).filter( and_(
                    Job.target_type == JOB_TARGET['INSTANCE'],
                    Job.target_id == instance.id) ).order_by(desc(Job.id)).first()
            instance.lastjob = old
            job = old

        if self.request.connection.stream.closed() or not job:
            return self.finish()

        self.db2.commit()


        if ( job.status == status.get('job', 0) and 
               instance.status == status.get('instance', 0) ):

            if job and job.completed and instance.is_running:
                time_interval = settings.INSTANCE_S_UP_INTER_2
            else:
                time_interval = settings.INSTANCE_S_UP_INTER_1

            tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + time_interval,
                lambda: self.check_status(instance, status) )

        else:

            istatus_imgurl = self.theme_url('icons/InstanceStatus/%s.png' % instance.status)
            if job.completed:
                if job.status >=600:
                    jstatus_imgurl = self.theme_url('icons/JobStatus/%s.png' % job.status)
                else:
                    jstatus_imgurl = self.theme_url('icons/JobStatus/completed.png')
            else:
                jstatus_imgurl = self.theme_url('icons/JobStatus/running.gif')

            ip, ip_link = '', ''
            domain, domain_link = '', ''

            if instance.work_ip:
                ip_link = instance.home_url(self.current_user)
                ip = instance.work_ip

            if instance.domain and instance.is_running:
                domain_link = instance.home_url(self.current_user)
                domain = instance.domain

            if instance.can_run:
                iaction = 'run'
            elif instance.need_query:
                iaction = 'query'
            else:
                iaction = 'stop'

            json = { 'job_id': job.id,

                     'jstatus': job.status,
                     'jstatus_str': job.status_string,
                     'istatus_imgurl': istatus_imgurl,

                     'istatus': instance.status,
                     'istatus_str': instance.status_string,
                     'jstatus_imgurl': jstatus_imgurl,

                     'ip': ip, 'ip_link': ip_link,
                     'domain': domain, 'domain_link': domain_link,

                     'job_completed': 1 if job.completed else 0,
                     'iaction': iaction }

            
            if job.status >= 300 and job.status <= 399:
                json['status'] = 0

            self.write(json)
            self.finish()


class CheckInstanceStatus(InstRequestHandler):

    ''' check instance dynamic status '''

    @asynchronous
    def post(self):

        WATCH = []

        self.body = json.loads( self.request.body )

        print '[DD] %s body = %s' % (datetime.now(), self.body)

        idata = self.body.get('instance', [])
        if idata and isinstance(idata, list):
            for si in idata:
                ID = self.get_int(si.get('id', 0))
                if ID:
                    i = self.db2.query(Instance).get(ID)
                    if i:
                        old_is = self.get_int(si.get('is', 0))
                        old_js = self.get_int(si.get('js', 0))
                        WATCH.append( (i, old_is, old_js) )

            if WATCH:
                return self.check_status(WATCH)

        self.write( { 'return_code': 1, 'upload_data': self.body } )
        return self.finish()


    def check_status(self, WATCH):

        if self.request.connection.stream.closed():
            return self.finish()

        self.db2.commit() # TODO: need sync now

        CHS = []
        show_job = self.get_int(self.body.get('show_job', 0))

        for instance, old_is, old_js in WATCH:

            print '[DD] id = %s, is = [%s, %s], js = [%s, %s]' % (instance.id, old_is, instance.status, old_js, instance.lastjob_status_id)

            if old_is and old_is != instance.status:
                CHS.append(instance)

            if show_job and old_js and instance.lastjob:
                if old_js != instance.lastjob.status:
                    CHS.append(instance)

        if CHS:
            ret = self.get_json_data(CHS)
            print '[DD] CHS = %s, ret = %s' % (CHS, ret)
            self.write( ret )
            self.finish()

        else:
            # Need sleep to wait change
            if instance.lastjob and not instance.lastjob.completed:
                time_interval = settings.INSTANCE_S_UP_INTER_1
            else:
                time_interval = settings.INSTANCE_S_UP_INTER_2
            #print '[DD] %s SLEEP %s seconds' % (datetime.now(), time_interval)

            tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + time_interval,
                lambda: self.check_status(WATCH) )


    def get_json_data(self, CHS):

        show_action = self.get_int(self.body.get('show_action', 0))
        show_domain = self.get_int(self.body.get('show_domain', 0))
        show_ip = self.get_int(self.body.get('show_ip', 0))
        show_job = self.get_int(self.body.get('show_job', 0))

        idata = []
        for instance in CHS:

            CS = { 'id': instance.id, 'is': instance.status,
                   'js': instance.lastjob_status_id,
                   'is_str': instance.status_string,
                   'is_img': self.theme_url('icons/InstanceStatus/%s.png' % instance.status) }

            # SHOW job status
            if show_job:
                CS['js_str'] = instance.job_status_string
                job = instance.lastjob
                if job and job.completed:
                    if job.status >=600:
                        CS['js_img'] = self.theme_url('icons/JobStatus/%s.png' % job.status)
                    else:
                        CS['js_img'] = self.theme_url('icons/JobStatus/completed.png')
                else:
                    CS['js_img'] = self.theme_url('icons/JobStatus/running.gif')

            # SHOW ip status
            if show_ip and instance.work_ip:
                CS['ip_link'] = instance.home_url(self.current_user)
                CS['ip'] = instance.work_ip

            # SHOW domain status
            if show_domain and instance.domain and instance.is_running:
                CS['domain_link'] = instance.home_url(self.current_user)
                CS['domain'] = instance.domain


            # SHOW control action status
            if show_action:
                if instance.can_run:
                    CS['iaction'] = 'run'
                elif instance.need_query:
                    CS['iaction'] = 'query'
                else:
                    CS['iaction'] = 'stop'

            idata.append( CS )

        return { 'return_code': 0, 'instance': idata }



class SingleInstanceStatus(InstRequestHandler):

    ''' check a instance status '''

    @asynchronous
    def post(self):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        data = json.loads( self.request.body )
        #print '[DD] %s body = %s' % (datetime.now(), data)

        ID = self.get_int( data.get('id', 0) )
        i = self.db2.query(Instance).get(ID)
        if i:
            self.check_status( {
                'instance': i,
                'old_is': self.get_int(data.get('is', 0)),
                'old_js': self.get_int(data.get('js', 0)) } )
        else:
            self.write( {'return_code': 1} )
            self.finish()


    def check_status(self, cs):

        if self.request.connection.stream.closed():
            return self.finish()

        self.db2.commit() # TODO: need sync now

        I = cs['instance']
        old_is = cs['old_is']
        old_js = cs['old_js']

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
               'is_str'      : I.status_string,

               'js'          : I.lastjob_status_id,
               'js_str'      : I.job_status_string,
               'lastjob'     : I.lastjob_id if I.lastjob_id else 0,

               'ip'          : '',
               'ip_link'     : '',
               'domain'      : '',
               'domain_link' : '' }

        CS['is_img'] = self.theme_url('icons/InstanceStatus/%s.png' % I.status)

        job = I.lastjob
        if job and job.completed:
            if job.status >=600:
                CS['js_img'] = self.theme_url('icons/JobStatus/%s.png' % job.status)
            else:
                CS['js_img'] = self.theme_url('icons/JobStatus/completed.png')
        else:
            CS['js_img'] = self.theme_url('icons/JobStatus/running.gif')

        if I.work_ip:
            CS['ip_link'] = I.home_url(self.current_user)
            CS['ip'] = I.work_ip

        if I.domain and I.is_running:
            CS['domain_link'] = I.home_url(self.current_user)
            CS['domain'] = I.domain

        if I.can_run:
            CS['iaction'] = 'run'
        elif I.need_query:
            CS['iaction'] = 'query'
        else:
            CS['iaction'] = 'stop'

        return CS
