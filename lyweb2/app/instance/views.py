# coding: utf-8

import logging, struct, socket
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

LST_WEB_S = 1
LST_CONTROL_S = 2
LST_COMPUTE_S = 3

RQTYPE_NEW_JOB = 10

LYJOB_STATUS = {
    'unknown': 0,
    'prepare': 1,
    'running': 2,
    'finished': 3,
    'failed': 4,
    'stoped': 5,
    'pending': 10,
}



LYJOB_TARGET_TYPE = {
    'unknown': 0,
    'node': 1,
    'instance': 2,
}


class Index(LyRequestHandler):

    @authenticated
    def get(self):

        insts = self.db.query(
            'SELECT * from instance WHERE user_id=%s;',
            self.current_user.id )

        for i in insts:
            i.appliance = self.db.get(
                'SELECT * from appliance WHERE id=%s;',
                i.appliance_id )
            if not i.appliance:
                logging.error('Query appliance from DB failed: %s' % emsg)

        d = { 'title': 'Instances Home', 'instances': insts }

        self.render('instance/index.html', **d)


class View(LyRequestHandler):

    def get(self, id):

        inst = self.db.get(
            'SELECT * from instance WHERE id=%s;', id )

        if not inst:
            return self.write('Have not found instance %s !' % id)

        inst.appliance = self.db.get(
            'SELECT * from appliance WHERE id=%s;',
            inst.appliance_id )

        d = { 'title': 'View Instance %s' % id,
              'instance': inst }

        self.render('instance/view.html', **d)


class Add(LyRequestHandler):

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

        d = { 'title': 'Create new instance',
              'name': name, 'app_id': app_id }

        if not (app_id and name):
            d['submit_error'] = 'name or appliance can not be empty !'
            return self.render('instance/add.html', **d)

        app = self.db.get(
            'SELECT * from appliance WHERE id=%s;', app_id )

        if not app:
            return self.write('Appliance %s does not exist !' % app_id)

        id_seq = self.db.get('SELECT last_value from instance_id_seq ;')
        print 'id_seq = ', id_seq
        next_id = id_seq.last_value + 1


        mac = '92:1B:40:26:%02x:%02x' % (
            next_id / 256, next_id % 256)

        self.db.execute(
            "INSERT INTO instance \
(name, user_id, appliance_id, mac, status, created, updated) \
VALUES (%s, %s, %s, %s, 1, 'now', 'now');",
            name, self.current_user.id, app_id, mac )

        inst = self.db.get(
            'SELECT id from instance WHERE mac=%s;', mac )

        self.redirect('/instance/%s' % inst.id)



class Edit(LyRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id=%s;', id)

        if not inst:
            return self.write('Have not found instance %d !' % id )

        if inst.user_id != self.current_user.id:
            return self.write('Just owner can do this !')

        d = { 'title': 'Edit Instance %s' % id,
              'instance': inst }

        self.render('instance/edit.html', **d)


    @authenticated
    def post(self, id):

        inst = self.db.get('SELECT * from instance WHERE id=%s;', id)

        if not inst:
            return self.write('Have not found instance %d !' % id )

        if inst.user_id != self.current_user.id:
            return self.write('Just owner can do this !')

        name = self.get_argument('name', '')
        cpus = int(self.get_argument('cpus', 0))
        memory = int(self.get_argument('memory', 0))

        d = { 'title': 'Edit Instance %s' % id,
              'instance': inst, 'name': name,
              'cpus': cpus, 'memory': memory }

        if not (name and cpus <= 4 and memory <= 1024):
            if not name:
                d['name_error'] = 'you must set name !'
            if cpus > 4:
                d['cpus_error'] = 'cpus (%s) is too large !' % cpus
            if memory > 1024:
                d['memory_error'] = 'memory (%s) is to large !' % memory
            return self.render('instance/edit.html', **d)

        self.db.execute(
            'UPDATE instance SET name=%s, cpus=%s, memory=%s WHERE id = %s',
            name, cpus, memory, id )

        self.redirect('/instance/%s' % id)


class Delete(LyRequestHandler):

    @authenticated
    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id=%s;', id)
        if not inst:
            return self.write('Have not found instance %s !' % id)

        if inst.user_id != self.current_user.id:
            return self.write('Just owner can do this !')

        self.db.execute(
            'DELETE FROM instance WHERE id=%s;', id )

        self.redirect('/instance')



class Control(LyRequestHandler):

    @authenticated
    @asynchronous
    def get(self, id, action):

        inst = self.db.get('SELECT * from instance WHERE id=%s;', id)

        if not inst:
            self.write('Have not found instance %s !' % id)
            return self.finish()

        if inst.user_id != self.current_user.id:
            self.write('Just owner can do this !')
            return self.finish()
        LYJOB_ACTION = self.application.settings['LYJOB_ACTION']
        action_id = LYJOB_ACTION.get(action, 0)
        if not action_id:
            self.write('Unknown action "%s" !' % action)
            return self.finish()

        target_type = LYJOB_TARGET_TYPE.get('instance', 0)
        status = LYJOB_STATUS.get('prepare', 0)

        try:
            self.db.execute(
                "INSERT INTO job (user_id, status, \
target_type, target_id, action, created) VALUES \
(%s, %s, %s, %s, %s, 'now');",
                self.current_user.id, status, target_type,
                id, action_id )
        except Exception, emsg:
            self.write('Create new job in DB failed: %s' % emsg)
            return self.finish()

        # TODO: get job id
        jobs = self.db.query(
            'SELECT id from job WHERE user_id = %s and \
status = %s and target_type = %s and target_id = %s and \
action = %s ORDER BY id;',
            self.current_user.id, status, target_type, id, action_id )

        rqhead = struct.pack('iiii', LST_WEB_S, RQTYPE_NEW_JOB, 4, jobs[-1].id)

        cip = self.application.settings['control_server_ip']
        cport = self.application.settings['control_server_port']
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.connect( (cip, cport) )
        sk.sendall(rqhead)
        sk.close()

        self.write('%s instance %s success !' % (action, id))
        self.finish()



class InstanceConfig(LyRequestHandler):

    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id = %s;', id)

        inst.appliance = self.db.get(
            'SELECT * from appliance WHERE id = %s;',
            inst.appliance_id )

        self.render('instance/config.txt', instance = inst)



class LibvirtdConf(LyRequestHandler):

    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id = %s;', id)

        inst.appliance = self.db.get(
            'SELECT * from appliance WHERE id = %s;',
            inst.appliance_id )

        self.set_header("Content-Type", "text/xml")
        self.render('instance/libvirtd_conf.xml', instance = inst)



class OsmanagerConf(LyRequestHandler):

    def get(self, id):

        inst = self.db.get('SELECT * from instance WHERE id = %s;', id)

        #self.set_header("Content-Type", "text")
        self.render( 'instance/osmanager.conf',
                     instance = inst,
                     control_server_ip = self.application.settings['control_server_ip'],
                     control_server_port = self.application.settings['control_server_port']
                     )
