# coding: utf-8

import os, logging

from lycustom import LyRequestHandler, Pagination
from tornado.web import authenticated

from sqlalchemy.sql.expression import asc, desc

from app.instance.models import Instance
from app.appliance.models import Appliance
from app.node.models import Node
from app.account.models import Permission

import settings



class Index(LyRequestHandler):

    def get(self):

        view = self.get_argument('view', 'self')
        by = self.get_argument('by', 'created')
        sort = self.get_argument('sort', 'DESC')
        page_size = int(self.get_argument('sepa', 10))
        cur_page = int(self.get_argument('p', 1))

        start = (cur_page - 1) * page_size
        stop = start + page_size

        instances = self.db2.query(Instance)
        if view == 'self' and self.current_user:
            instances = instances.filter_by(
                user_id=self.current_user.id )
        instances = instances.slice(start, stop)

        # TODO:


        if self.current_user and view == 'self':
            USED_INSTANCE = self.db2.query(Instance.id).filter(
                Instance.user_id == self.current_user.id).count()
            TOTAL_APPLIANCE = self.db2.query(Appliance.id).filter(
                Appliance.user_id == self.current_user.id).count()
        else:
            USED_INSTANCE = self.db2.query(Instance.id).count()
            TOTAL_APPLIANCE = 0

        page_html = Pagination(
            total = USED_INSTANCE,
            page_size = page_size,
            cur_page = cur_page ).html(self.get_page_url)

        TOTAL_CPU = 0
        TOTAL_MEMORY = 0
        TOTAL_INSTANCE = 0
        if self.current_user:
            if self.current_user.profile:
                TOTAL_CPU = self.current_user.profile.cpus
                TOTAL_MEMORY = self.current_user.profile.memory
                TOTAL_INSTANCE = self.current_user.profile.instances
            # TODO: a temp hack
            else:
                TOTAL_CPU = 8
                TOTAL_MEMORY = 4096
                TOTAL_INSTANCE = 20

        USED_CPU = 0
        USED_MEMORY = 0
        if self.current_user:
            insts = self.db2.query(Instance).filter(
                Instance.user_id == self.current_user.id)
            for i in insts:
                if i.status in [4, 5]:
                    USED_CPU += i.cpus
                    USED_MEMORY += i.memory

        d = { 'title': _('LuoYun Home'),
              'TOTAL_CPU': TOTAL_CPU,
              'TOTAL_MEMORY': TOTAL_MEMORY,
              'USED_CPU': USED_CPU,
              'USED_MEMORY': USED_MEMORY,
              'TOTAL_APPLIANCE': TOTAL_APPLIANCE,
              'USED_INSTANCE': USED_INSTANCE,
              'TOTAL_INSTANCE': TOTAL_INSTANCE,
              'INSTANCE_LIST': instances,
              'cur_page': cur_page,
              'page_html': page_html }

        self.render("home/index.html", **d)



class SetLocale(LyRequestHandler):

    def get(self):

        user_locale = self.get_argument("language")
        next_url = self.get_argument("next", '/')
        self.set_cookie("user_locale", user_locale)

        self.redirect(next_url)


class NoPermission(LyRequestHandler):

    def get(self):

        PERMS = []

        codenames = self.get_argument('codenames', '')
        for cn in codenames.split(','):
            p = self.db2.query(Permission).filter_by(
                codename = cn ).first()
            if p:
                PERMS.append(p)
            else:
                logging.error('No such permission: %s' % cn)


        if hasattr(settings, 'ADMIN_EMAIL'):
            ADMIN_EMAIL = settings.ADMIN_EMAIL
        else:
            ADMIN_EMAIL = 'contact@luoyun.co'

        d = { 'title': _("Permission Denied"),
              'ADMIN_EMAIL': ADMIN_EMAIL,
              'PERMS': PERMS }

        self.set_status(403)
        self.render('home/no_permission.html', **d)


class NoResource(LyRequestHandler):

    def get(self):

        reason = self.get_argument('reason', '')

        d = { 'title': _("No Resource"),
              'REASON': reason }

        insts = self.db2.query(Instance).filter(
            Instance.user_id == self.current_user.id )
        d['USED_INSTANCES'] = insts.count()
        d['USED_CPUS'] = 0
        d['USED_MEMORY'] = 0
        for i in insts:
            if i.status in [4, 5]:
                d['USED_CPUS'] += i.cpus
                d['USED_MEMORY'] += i.memory

        self.render('home/no_resource.html', **d)
