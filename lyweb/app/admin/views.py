# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.instance.models import Instance
from app.appliance.models import Appliance
from app.node.models import Node
from app.account.models import User
from app.job.models import Job

from lycustom import has_permission

from sqlalchemy.sql.expression import asc, desc

from lytool.filesize import size as human_size



class Index(LyRequestHandler):

    @has_permission('admin')
    def get(self):

        # TODO:
        TOTAL_INSTANCE = self.db2.query(Instance.id).count()
        TOTAL_APPLIANCE = self.db2.query(Appliance.id).count()

        # CPUS and Memory
        nodes = self.db2.query(Node).filter_by(isenable=True)
        TOTAL_CPU = 0
        TOTAL_MEMORY = 0
        for n in nodes:
            TOTAL_CPU += n.cpus
            TOTAL_MEMORY += n.memory

        insts = self.db2.query(Instance).filter(
            Instance.status == 4 or Instance.status == 5
            ).all()

        USED_CPU = 0
        USED_MEMORY = 0
        RUNNING_INSTANCE = 0
        for i in insts:
            USED_CPU += i.cpus
            RUNNING_INSTANCE += 1
            USED_MEMORY += i.memory * 1024

        new_users = self.db2.query(User).order_by(
            desc(User.id) ).limit(10)
        new_jobs = self.db2.query(Job).order_by(
            desc(Job.id) ).limit(10)

        d = { 'title': _('Admin Console'),
              'human_size': human_size,
              'TOTAL_APPLIANCE': TOTAL_APPLIANCE,
              'TOTAL_INSTANCE': TOTAL_INSTANCE,
              'TOTAL_CPU': TOTAL_CPU * 16, # TODO: a temp hack
              'TOTAL_MEMORY': TOTAL_MEMORY,
              'USED_CPU': USED_CPU,
              'USED_MEMORY': USED_MEMORY,
              'RUNNING_INSTANCE': RUNNING_INSTANCE,
              'NEW_USER_LIST': new_users,
              'NEW_JOB_LIST': new_jobs }

        self.render('admin/index.html', **d)





class AccountIndex(LyRequestHandler):

    @has_permission('admin')
    def get(self):
        self.render('admin/account.html')

