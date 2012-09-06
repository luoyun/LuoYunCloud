# coding: utf-8

from datetime import datetime
from lycustom import LyRequestHandler, Pagination

from app.account.models import User, ApplyUser, UserProfile
from app.instance.models import Instance
from app.appliance.models import Appliance, ApplianceCatalog

import tornado
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc

from settings import INSTANCE_DELETED_STATUS as DELETED_S

import settings


class Index(LyRequestHandler):

    @authenticated
    def get(self):

        my = self.db2.query(User).get(self.current_user.id)
        d = { 'my': my }

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
        page_size = int(self.get_argument(
                'sepa', settings.MYUN_INSTANCE_LIST_PAGE_SIZE))
        cur_page = int(self.get_argument('p', 1))

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

        if total > page_size:
            page_html = Pagination(
                total = total,
                page_size = page_size,
                cur_page = cur_page ).html(self.get_page_url)
        else:
            page_html = ""

        return instances, page_html



class MyunAppliance(LyRequestHandler):

    @authenticated
    def get(self):

        apps, page_html = self.page_view_my_appliances()

        d = { 'title': _('My Appliances'),
              'APPLIANCE_LIST': apps, 'page_html': page_html }

        self.render( 'myun/appliances.html', **d)


    def page_view_my_appliances(self):

        catalog_id = int( self.get_argument('c', 1) )
        page_size = int( self.get_argument('sepa', 10) )
        cur_page = int( self.get_argument('p', 1) )
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        apps = self.db2.query(Appliance).filter_by(
            catalog_id=catalog_id).filter_by(
            user_id=self.current_user.id).order_by(by_exp)

        total = apps.count()
        apps = apps.slice(start, stop)
            
        catalogs = self.db2.query(ApplianceCatalog).all()
        for c in catalogs:
            c.total = self.db2.query(Appliance.id).filter_by( catalog_id = c.id ).count()

        pagination = Pagination(
            total = total, page_size = page_size, cur_page = cur_page )

        page_html = pagination.html( self.get_page_url )

        return apps, page_html
