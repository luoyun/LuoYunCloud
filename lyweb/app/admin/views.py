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

        new_users = self.db2.query(User).order_by(
            desc(User.id) ).limit(10)
        new_jobs = self.db2.query(Job).order_by(
            desc(Job.id) ).limit(10)

        d = { 'title': self.trans(_('Admin Console')),
              'human_size': human_size,
              'TOTAL_APPLIANCE': TOTAL_APPLIANCE,
              'TOTAL_INSTANCE': TOTAL_INSTANCE,
              'NEW_USER_LIST': new_users,
              'NEW_JOB_LIST': new_jobs,
              'chart_data': self.chart_data }

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


    def chart_data(self, what=None):
        if not what: return

        ud = self._get_data()
        if not ud: return

        profile = self.current_user.profile

        d = { 'subcaption': self.trans(_("TOTAL: ")),
              'name1': self.trans(_("Used")),
              'name2': self.trans(_("Unused")) }
        number_suffix = ''

        if what == 'cpu':
            caption = self.trans(_("CPU USED INFO"))
            total = '%s CPU' % ud['TOTAL_CPU']
            value1 = ud['USED_CPU']
            value2 = ud['TOTAL_CPU'] - ud['USED_CPU']
            number_suffix = self.trans(_("core"))
        elif what == 'memory':
            caption = self.trans(_("MOMORY USED INFO"))
            total = human_size(ud['TOTAL_MEMORY']*1024*1024)
            value1 = ud['USED_MEMORY']
            value2 = ud['TOTAL_MEMORY'] - ud['USED_MEMORY']
            number_suffix = "M"
        else:
            return

        d.update({ 'caption': caption, 'total': total,
                   'value1': value1, 'value2': value2,
                   'number_suffix': number_suffix })

        T = '<graph caption="%(caption)s" \
subCaption="%(subcaption)s %(total)s" \
showNames="1" bgColor="F4F8FC" decimalPrecision="0" \
formatNumberScale="0" baseFontSize="16" \
numberSuffix="%(number_suffix)s">\
<set name="%(name1)s" value="%(value1)s" color="FC0101" />\
<set name="%(name2)s" value="%(value2)s" color="AFD8F8" /></graph>'

        return T % d




class AccountIndex(LyRequestHandler):

    @has_permission('admin')
    def get(self):
        self.render('admin/account.html')

