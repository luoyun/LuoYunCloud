# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import LyRequestHandler
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
        TOTAL_USER = self.db2.query(User.id).count()
        TOTAL_JOB = self.db2.query(Job.id).count()
        TOTAL_NODE = self.db2.query(Node.id).count()

        new_users = self.db2.query(User).order_by(
            desc(User.id) ).limit(10)
        new_jobs = self.db2.query(Job).order_by(
            desc(Job.id) ).limit(10)

        ud = self._get_data()

        d = { 'title': self.trans(_('Admin Console')),
              'human_size': human_size,
              'TOTAL_APPLIANCE': TOTAL_APPLIANCE,
              'TOTAL_INSTANCE': TOTAL_INSTANCE,
              'TOTAL_USER': TOTAL_USER,
              'TOTAL_JOB': TOTAL_JOB,
              'TOTAL_NODE': TOTAL_NODE,
              'NEW_USER_LIST': new_users,
              'NEW_JOB_LIST': new_jobs,
              'TOTAL_MEMORY': ud['TOTAL_MEMORY'],
              'USED_MEMORY': ud['USED_MEMORY'],
              'USED_MEMORY_P': ud['USED_MEMORY'] * 100.0 / ud['TOTAL_MEMORY'],
              'TOTAL_CPU': ud['TOTAL_CPU'],
              'USED_CPU': ud['USED_CPU'],
              'USED_CPU_P': ud['USED_CPU'] * 100.0 / ud['TOTAL_CPU']}

        d.update( self._get_data() )

        self.render('admin/index.html', **d)

    def _get_data(self):

        if hasattr(self, 'system_data') and self.system_data:
            return self.system_data

        # CPUS and Memory
        nodes = self.db2.query(Node).filter_by(isenable=True)
        TOTAL_CPU = 0
        TOTAL_MEMORY = 0
        for n in nodes:
            TOTAL_CPU += self.get_int(n.vcpus, 0)
            TOTAL_MEMORY += self.get_int(n.vmemory, 0)

        insts = self.db2.query(Instance).filter(
            Instance.status == 4 or Instance.status == 5 )

        USED_CPU = 0
        USED_MEMORY = 0

        for i in insts:
            USED_CPU += i.cpus
            USED_MEMORY += i.memory * 1024

        self.system_data = {
            'TOTAL_CPU': TOTAL_CPU,
            'TOTAL_MEMORY': TOTAL_MEMORY,
            'USED_CPU': USED_CPU,
            'USED_MEMORY': USED_MEMORY }

        return self.system_data



class AccountIndex(LyRequestHandler):

    @has_permission('admin')
    def get(self):
        self.render('admin/account.html')

