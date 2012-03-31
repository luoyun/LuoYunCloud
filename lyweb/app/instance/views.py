# coding: utf-8

import logging, struct, socket, re, Image, os
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from settings import JOB_ACTION, JOB_TARGET


class InstRequestHandler(LyRequestHandler):

    def initialize(self):
        self.view_kwargs = {
            'isrunning': self.isrunning,
            }

    def isrunning(self, status):

        return status in [ 3, 4, 5 ]


    def create_logo(self, app, inst_id):
        ''' Create logo '''

        if not app.logoname:
            return False

        applogo = os.path.join(
            self.settings['appliance_top_dir'],
            app.logoname )

        if not os.path.exists(applogo):
            logging.error('%s not exist' % applogo)
            return False

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
        print 'HERE7'

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

        inst = self.db.get(
            'SELECT * from instance WHERE id=%s;', id )

        if not inst:
            return self.done( _('No instance %s !') % id )

        inst.user = self.db.get(
            'SELECT * FROM auth_user WHERE id=%s;',
            inst.user_id )
        inst.appliance = self.db.get(
            'SELECT * from appliance WHERE id=%s;',
            inst.appliance_id )

        # TODO: recently job list
        JOB_LIST = self.db.query(
            'SELECT * FROM job \
WHERE target_id=%s and target_type=%s \
ORDER BY created DESC LIMIT 5;',
            id, JOB_TARGET['INSTANCE'] )

        for J in JOB_LIST:
            J.user = self.db.get(
                'SELECT id, username FROM auth_user \
WHERE id=%s;', J.user_id )
            J.result = self.job_status(J.status)

        d = { 'title': 'View Instance %s' % id,
              'instance': inst,
              'instance_logo_url': self.instance_logo_url,
              'JOB_LIST': JOB_LIST,
              'job_action': self.job_action }

        if self.get_argument('ajax', 0):
            self.render('instance/view_by_ajax.html', **d)
        else:
            self.render('instance/view.html', **d)




class Add(InstRequestHandler):


    @authenticated
    def get(self):

        apps = self.db.query('SELECT * from appliance;')

        d = { 'title': 'Create new instance',
              'appliances': apps }

        self.render('instance/add.html', **d)


    @authenticated
    def post(self):

        app_id = int(self.get_argument('appliance', 0))
        name = self.get_argument('name', '')

        d = { 'title': 'Create new instance', 'ERROR': [],
              'name': name, 'app_id': app_id }

        if not app_id:
            d['ERROR'].append(u'appliance needed')
        if not name:
            d['ERROR'].append(u'name needed')

        if d['ERROR']:
            return self.render('instance/add.html', **d)

        app = self.db.get(
            'SELECT * from appliance WHERE id=%s;', app_id )

        if not app:
            return self.write('No appliance %s!' % app_id)

        try:
            r = self.db.query(
            "INSERT INTO instance (name, user_id, \
appliance_id, status, created, updated) \
VALUES (%s, %s, %s, 1, 'now', 'now') RETURNING id;",
            name, self.current_user.id, app_id )

            inst_id = r[0].id

            mac = '92:1B:40:26:%02x:%02x' % (
                inst_id / 256, inst_id % 256 )

            self.db.execute(
                'UPDATE instance SET mac=%s WHERE id=%s;',
                mac, inst_id )

            sname = self.create_logo(app, inst_id)
            if sname:
                self.db.execute(
                    'UPDATE instance SET logo=%s \
WHERE id=%s;',
                    sname, inst_id )

            self.redirect('/instance/%s' % inst_id)


        except Exception, emsg:
            return self.write(u'System error: %s' % emsg)





class Edit(InstRequestHandler):


    def initialize(self):

        self.d = { 'title': 'Edit Instance', 'ERROR': [],
                   'instance_logo_url': self.instance_logo_url }
        self.t = 'instance/edit.html'


    @authenticated
    def prepare(self):

        id = re.match('.*/([0-9]+)/.*', self.request.path).groups()[0]

        inst = self.db.get(
            'SELECT * from instance WHERE id=%s;', id)

        if not inst:
            self.write('Have not found instance %d !' % id )
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

        self.db.execute(
            "UPDATE instance SET \
name=%s, cpus=%s, memory=%s, updated='now' WHERE id = %s",
            name, cpus, memory, id )

        self.redirect('/instance/%s' % id)



class Delete(InstRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.db.get(
            'SELECT * from instance WHERE id=%s;', id)

        if not inst:
            return self.done( _('No instance %s !') % id )

        if self.current_user.id not in [inst.user_id, 1]:
            return self.done( _('No permissions !') )

        self.db.execute(
            'DELETE FROM instance WHERE id=%s;', id )

        return self.done( _('Delete instance %s success !' % id) )




class Control(InstRequestHandler):


    @authenticated
    def get(self, id, action):

        inst = self.db.get(
            'SELECT * from instance WHERE id=%s;', id)

        if not inst:
            return self.write( _('No instance %s !') % id )

        if self.current_user.id not in [inst.user_id, 1]:
            return self.write( _('No permissions !') )

        LYJOB_ACTION = self.settings['LYJOB_ACTION']
        action_id = LYJOB_ACTION.get(action, 0)
        if not action_id:
            return self.write( _('Unknown action "%s" !') % action )

        # TODO: not run instance that it's running, and stop
        if ( ( action_id == 201 and 
               inst.status not in [0, 1, 2, 9] ) or (
                action_id == 202 and 
                inst.status in [0, 1, 2, 9] ) ):
            return self.write(
                _('the status of instance %s is: "%s", can not %s') % (
                    id, self.instance_status(inst.status), 
                    self.job_action(action_id) ) )

        jid = self.new_job(JOB_TARGET['INSTANCE'], id, action_id)

        ajax = self.get_argument('ajax', 0)
        desc = u'%s instance %s success !' % (action, id)

        if ajax:
            json = { 'jid': jid, 'desc': desc }
            self.write(json)
        else:
            self.write(desc)



class InstanceConfig(InstRequestHandler):

    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id = %s;', id)

        inst.appliance = self.db.get(
            'SELECT * from appliance WHERE id = %s;',
            inst.appliance_id )

        self.render('instance/config.txt', instance = inst)



class LibvirtdConf(InstRequestHandler):

    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id = %s;', id)

        inst.appliance = self.db.get(
            'SELECT * from appliance WHERE id = %s;',
            inst.appliance_id )

        self.set_header("Content-Type", "text/xml")
        self.render('instance/libvirtd_conf.xml', instance = inst)



class OsmanagerConf(InstRequestHandler):

    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id = %s;', id)

        #self.set_header("Content-Type", "text")
        self.render( 'instance/osmanager.conf',
                     instance = inst,
                     control_server_ip = self.application.settings['control_server_ip'],
                     control_server_port = self.application.settings['control_server_port']
                     )
