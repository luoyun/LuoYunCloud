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



class Action(LyRequestHandler):

    @authenticated
    def get(self, id):

        action = int(self.get_argument("action", 0))

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
