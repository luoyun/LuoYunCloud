# coding: utf-8

import os, logging, json

from lycustom import LyRequestHandler, Pagination
from tornado.web import authenticated

from sqlalchemy.sql.expression import asc, desc

from app.instance.models import Instance
from app.appliance.models import Appliance
from app.node.models import Node
from app.account.models import Permission
from app.system.models import LuoYunConfig

import settings

from lycustom import has_permission


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
              'ADMIN_ID': 1,
              'PERMS': PERMS }

        self.set_status(403)
        self.render('home/no_permission.html', **d)


class NoResource(LyRequestHandler):

    def get(self):

        reason = self.get_argument('reason', '')

        d = { 'title': _("No Resource"),
              'REASON': reason,
              'USED_STORAGE': self.get_argument('used', 0)}

        insts = self.db2.query(Instance).filter(
            Instance.user_id == self.current_user.id )
        d['USED_INSTANCES'] = insts.count()
        d['USED_CPUS'] = 0
        d['USED_MEMORY'] = 0
        for i in insts:
            if i.status in [4, 5]:
                d['USED_CPUS'] += i.cpus
                d['USED_MEMORY'] += i.memory

        if hasattr(settings, 'ADMIN_EMAIL'):
            d['ADMIN_EMAIL'] = settings.ADMIN_EMAIL
        else:
            d['ADMIN_EMAIL'] = 'contact@luoyun.co'

        d['ADMIN_ID'] = 1

        self.render('home/no_resource.html', **d)



class RegistrationProtocol(LyRequestHandler):

    def get(self):

        protocol = self.db2.query(LuoYunConfig).filter_by(key='protocol').first()
        if protocol:
            rp = json.loads(protocol.value).get('html')
        else:
            rp = None

        self.render( 'home/registration_protocol.html',
                     REGISTRATION_PROTOCOL = rp )



class WelcomeNewUser(LyRequestHandler):

    # just admin can view this
    @has_permission('admin')
    def get(self):

        welcome = self.db2.query(LuoYunConfig).filter_by(key='welcome_new_user').first()
        if welcome:
            wc = json.loads(welcome.value).get('html')
        else:
            wc = None

        self.render( 'home/welcome.html',
                     WELCOME = wc )
