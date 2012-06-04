# coding: utf-8

import logging, struct, socket, re, os
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc

from app.appliance.models import Appliance
from app.instance.models import Instance
from app.job.models import Job
from app.instance.forms import CreateInstanceBaseForm, CreateInstanceForm


from settings import JOB_ACTION, JOB_TARGET

IMAGE_SUPPORT=True
try:
    import Image
except ImportError:
    IMAGE_SUPPORT=False


class InstRequestHandler(LyRequestHandler):

    def initialize(self):
        self.view_kwargs = {
            'isrunning': self.isrunning,
            }

    def isrunning(self, status):

        return status in [ 3, 4, 5 ]


    def create_logo(self, app, inst_id):
        ''' Create logo '''

        if not hasattr(app, 'logoname'):
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

        ajax = int(self.get_argument('ajax', 0))

        if ajax:
            self.write(msg)
        else:
            self.render( 'instance/action_result.html',
                         msg = msg )



class View(InstRequestHandler):


    def get(self, id):

        inst = self.db2.query(Instance).get(id)
        if not inst:
            return self.done( _('No such instance: %s !') % id )

        JOB_LIST = self.db2.query(Job).filter(
            Job.target_id == id,
            Job.target_type == JOB_TARGET['INSTANCE'] )
        JOB_LIST.order_by( desc('created') )
        JOB_LIST = JOB_LIST.limit(5)

        d = { 'title': 'View Instance %s' % id,
              'instance': inst,
              'JOB_LIST': JOB_LIST }

        if self.get_argument('ajax', 0):
            self.render('instance/view_by_ajax.html', **d)
        else:
            self.render('instance/view.html', **d)




class Edit(InstRequestHandler):


    def initialize(self):

        self.d = { 'title': 'Edit Instance', 'ERROR': [], }
        self.t = 'instance/edit.html'


    @authenticated
    def prepare(self):

        id = re.match('.*/([0-9]+)/.*', self.request.path).groups()[0]

        inst = self.db2.query(Instance).get(id)

        if not inst:
            self.write('Have not found instance %s !' % id )
            return self.finish()

        if self.current_user.id not in [inst.user_id, 1]:
            self.write('No permissions !')
            return self.finish()

        self.d['instance'] = inst
        self.d['name'] = inst.name
        self.d['cpus'] = inst.cpus
        self.d['memory'] = inst.memory


    def get(self, id):

        self.render(self.t, **self.d)


    def post(self, id):

        name = self.get_argument('name', '')
        cpus = int(self.get_argument('cpus', 0))
        memory = int(self.get_argument('memory', 0))

        self.d['name'] = name
        self.d['cpus'] = cpus
        self.d['memory'] = memory

        if not name:
            self.d['ERROR'].append(u'you must set name !')
        if cpus > 4:
            self.d['ERROR'].append(
                u'cpus (%s) is too large !' % cpus )
        if memory > 1024:
            self.d['ERROR'].append(
                u'memory (%s) is to large !' % memory )

        if self.d['ERROR']:
            return self.render(self.t, **self.d)

        inst = self.db2.query(Instance).get(id)
        inst.name = name,
        inst.cpus = cpus,
        inst.memory = memory,
        self.db2.commit()
        self.redirect('/instance/%s' % id)



class Delete(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.db2.query(Instance).get(id)
        if not inst:
            return self.done( _('No instance %s !') % id )

        if self.current_user.id not in [inst.user_id, 1]:
            return self.done( _('No permissions !') )

        self.db2.delete(inst)
        self.db2.commit()

        return self.done( _('Delete instance %s success !' % id) )



class Control(InstRequestHandler):


    @authenticated
    def get(self, id, action):

        inst = self.db2.query(Instance).get(id)
        if not inst:
            return self.write( _('No instance %s !') % id )

        if not ( self.current_user.id == inst.user_id or
                 self.has_permission('admin') ):
            return self.write( _('No permissions !') )

        if action == 'run' and not self.have_resource(inst):
            return self.finish()

        LYJOB_ACTION = self.settings['LYJOB_ACTION']
        action_id = LYJOB_ACTION.get(action, 0)
        if not action_id:
            return self.write( _('Unknown action "%s" !') % action )

        # TODO: not run instance that it's running, and stop
        if ( ( action=='stop' and not inst.can_stop ) or (
                action=='run' and not inst.can_run ) ):
            return self.write(
                _('status of instance %s is "%s", can not %s') % (
                    id, inst.status_string(), action ) )

        job = Job( user = self.current_user,
                   target_type = JOB_TARGET['INSTANCE'],
                   target_id = id,
                   action = action_id )

        self.db2.add(job)
        self.db2.commit()
        self._job_notify( job.id )

        ajax = self.get_argument('ajax', 0)
        desc = u'%s instance %s success !' % (action, id)

        if ajax:
            json = { 'jid': job.id, 'desc': desc }
            self.write(json)
        else:
            self.write(desc)


    def have_resource(self, inst):
        # Have resources ?
        USED_INSTANCES = self.db2.query(Instance).filter(
            Instance.user_id == self.current_user.id).all()
        USED_CPUS = inst.cpus
        USED_MEMORY = inst.memory
        for I in USED_INSTANCES:
            if I.is_running:
                USED_CPUS += I.cpus
                USED_MEMORY += I.memory

        if ( USED_CPUS > self.current_user.profile.cpus or
             USED_MEMORY > self.current_user.profile.memory ):

            desc = _('No resources to run instance:')

            if USED_CPUS > self.current_user.profile.cpus:
                desc += _('the total cpus you owned is %s, but now were used %s.') % (self.current_user.profile.cpus, USED_CPUS - inst.cpus)
            if USED_MEMORY > self.current_user.profile.memory:
                desc += _('the total memory you owned is %s MB, but now were used %s MB.') % (self.current_user.profile.memory, USED_MEMORY - inst.memory)

            ajax = self.get_argument('ajax', 0)

            if ajax:
                json = { 'jid': 0, 'desc': desc }
                self.write(json)
            else:
                url = self.get_no_resource_url()
                url += "?reason=Resource Limit"
                self.redirect( url )

            return False

        return True



from lycustom import has_permission
class CreateInstance(InstRequestHandler):

    @has_permission('instance.create')
    def prepare(self):

        _id = self.get_argument('appliance_id', 0)
        self.appliance = self.db2.query(Appliance).get(_id)

        # Have resources ?
        USED_INSTANCES = self.db2.query(Instance.id).filter(
            Instance.user_id == self.current_user.id ).count()

        if USED_INSTANCES + 1 > self.current_user.profile.instances:
            url = self.get_no_resource_url()
            url += "?reason=Resource Limit"
            self.redirect( url )
            return self.finish()


    def get(self):
 
        if not self.appliance:
            form = CreateInstanceForm()
            apps = self.db2.query(Appliance)
            if not apps.count():
                return self.write( _("No appliances found, please upload a appliance first !") )
            form.appliance.query = apps.all()
        else:
            form = CreateInstanceBaseForm()
            form.name.data = self.appliance.name

        self.render( 'instance/create.html', title = _('Create Instance'),
                     form = form, appliance = self.appliance )


    def post(self):

        if not self.appliance:
            form = CreateInstanceForm( self.request.arguments )
            form.appliance.query = self.db2.query(Appliance).all()
            #app = self.db2.query(Appliance).get( form.appliance.data )e
            app = form.appliance.data
        else:
            form = CreateInstanceBaseForm( self.request.arguments )
            app = self.appliance 

        if form.validate():
            instance = Instance(
                name=form.name.data, user=self.current_user,
                appliance=app )

            self.db2.add(instance)
            self.db2.commit()
            instance.logo = self.create_logo(app, instance.id)
            self.db2.commit()

            instance.mac = '92:1B:40:26:%02x:%02x' % (
                instance.id / 256, instance.id % 256 )
            self.db2.commit()

            url = self.reverse_url('instance:view', instance.id)
            return self.redirect(url)

        self.render( 'instance/create.html', title = _('Create Instance'),
                     form = form, appliance = app )

        
            

