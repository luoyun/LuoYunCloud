# coding: utf-8

import struct, socket
import logging, datetime, time
import tornado
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from settings import JOB_ACTION, JOB_TARGET

from app.instance.models import Instance
from app.node.models import Node
from app.job.models import Job

from app.node.forms import NodeEditForm

from lycustom import has_permission



class Action(LyRequestHandler):

    @authenticated
    def get(self, id):

        action = self.get_argument_int("action", 0)

        node = self.db2.query(Node).get(id)
        if not node:
            return self.write('No such node!')

        if not action:
            return self.write( _("No action specified") )

        elif action == 1:
            if node.isenable:
                return self.write('Already enable !')
            else:
                action_id = JOB_ACTION['ENABLE_NODE']
                #self.new_job(JOB_TARGET['NODE'], id, JOB_ACTION['ENABLE_NODE'])

        elif action == 2:
            if not node.isenable:
                return self.write('Already disable !')
            else:
                action_id = JOB_ACTION['DISABLE_NODE']
                #self.new_job(JOB_TARGET['NODE'], id, JOB_ACTION['DISABLE_NODE'])
        else:
            return self.write('Unknow action!')


        job = Job( user = self.current_user,
                   target_type = JOB_TARGET['NODE'],
                   target_id = id,
                   action = action_id )
        self.db2.add(job)
        self.db2.commit()
        self._job_notify( job.id )

        return self.write('Action success !')



class isenableToggle(LyRequestHandler):

    @has_permission('admin')
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        N = self.db2.query(Node).get(ID)
        if not N:
            return self.write( _('Can not find node %s.') % ID )

        action_id = JOB_ACTION['DISABLE_NODE'] if N.isenable else JOB_ACTION['ENABLE_NODE']

        job = Job( user = self.current_user,
                   target_type = JOB_TARGET['NODE'],
                   target_id = ID,
                   action = action_id )

        self.db2.add(job)
        self.db2.commit()

        try:
            self._job_notify( job.id )

            N.isenable = not N.isenable
            self.db2.commit()
            # no news is good news

        except Exception, e:
            self.write( _('Run job failed: %s') % e )



class NodeEdit(LyRequestHandler):

    @has_permission('admin')
    def get(self, ID):

        N = self.db2.query(Node).get(ID)
        if not N:
            return self.write( _('Can not find node %s.') % ID )

        form = NodeEditForm(self)
        form.vmemory.data = (N.vmemory if N.vmemory else N.memory)  / (1024 * 1024)
        form.vcpus.data = N.vcpus if N.vcpus else N.cpus

        d = { 'title': _('Edit note configure'),
              'form': form, 'N': N }
        self.render('node/edit.html', **d)


    @has_permission('admin')
    def post(self, ID):

        N = self.db2.query(Node).get(ID)
        if not N:
            return self.write( _('Can not find node %s.') % ID )

        ERROR = []
        form = NodeEditForm(self)
        if form.validate():
            # TODO: check the node ability !
            N.vmemory = form.vmemory.data * 1024 * 1024 # KB
            N.vcpus = form.vcpus.data

            job = Job( user = self.current_user,
                       target_type = JOB_TARGET['NODE'],
                       target_id = ID,
                       action = JOB_ACTION.get('UPDATE_NODE') )

            self.db2.add(job)
            self.db2.commit()

            try:
                self._job_notify( job.id )
                url = self.reverse_url('admin:node')
                return self.redirect(url)
            except Exception, e:
                ERROR.append( _('Run job failed: %s') % e )

        d = { 'title': _('Edit note configure'),
              'form': form, 'N': N, 'ERROR': ERROR }
        self.render('node/edit.html', **d)
