# coding: utf-8

import os, logging, json, time

from tornado.web import authenticated

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_

from app.instance.models import Instance
from app.appliance.models import Appliance
from app.node.models import Node
from app.auth.models import Permission
from app.system.models import LuoYunConfig

import settings

from lycustom import RequestHandler, has_permission

from ..site.models import SiteEntry, SiteArticle
from ..language.models import Language


class Index(RequestHandler):

    title = _('LuoYunCloud Home')

    def get(self):

        E = self.db.query(SiteEntry).filter_by(slug='home').first()
        L = self.db.query(Language).filter_by(
            codename = self.locale.code ).first()
        if E and L:
            A = self.db.query(SiteArticle).filter(
                and_( SiteArticle.entry_id == E.id,
                      SiteArticle.language_id == L.id ) ).first()
        else: A = None

        d = {}

        if A:
            d['mainbody'] = A.body

        self.render('home/index.html', **d)


class SetLocale(RequestHandler):

    def get(self):

        user_locale = self.get_argument("language", self.locale.code)
        next_url = self.get_argument("next", '/')
        self.set_cookie("user_locale", user_locale)
        self.redirect(next_url)


class NoPermission(RequestHandler):

    def get(self):

        PERMS = []

        codenames = self.get_argument('codenames', '')
        for cn in codenames.split(','):
            p = self.db.query(Permission).filter_by(
                codename = cn ).first()
            if p:
                PERMS.append(p)
            else:
                logging.error('No such permission: %s' % cn)


        if hasattr(settings, 'ADMIN_EMAIL'):
            ADMIN_EMAIL = settings.ADMIN_EMAIL
        else:
            ADMIN_EMAIL = 'contact@luoyun.co'

        d = { 'title': self.trans(_("Permission Denied")),
              'ADMIN_EMAIL': ADMIN_EMAIL,
              'ADMIN_ID': 1,
              'PERMS': PERMS }

        self.set_status(403)
        self.render('home/no_permission.html', **d)


class NoResource(RequestHandler):

    title = _('No Resource')

    @authenticated
    def get(self):

        profile = self.current_user.profile
        # TODO: profile is None

        resource_total = profile.get_resource_total()
        resource_used = profile.get_resource_used()

        d = { 'resource_total': resource_total,
              'resource_used': resource_used,
              'REASON': self.get_argument('reason', '') }

        if hasattr(settings, 'ADMIN_EMAIL'):
            d['ADMIN_EMAIL'] = settings.ADMIN_EMAIL
        else:
            d['ADMIN_EMAIL'] = 'contact@luoyun.co'

        d['ADMIN_ID'] = 1

        self.render('home/no_resource.html', **d)



class RegistrationProtocol(RequestHandler):

    def get(self):

        protocol = self.db.query(LuoYunConfig).filter_by(key='protocol').first()
        if protocol:
            rp = json.loads(protocol.value).get('html')
        else:
            rp = None

        self.render( 'home/registration_protocol.html',
                     REGISTRATION_PROTOCOL = rp )



class WelcomeNewUser(RequestHandler):

    # just admin can view this
    @has_permission('admin')
    def get(self):

        welcome = self.db.query(LuoYunConfig).filter_by(key='welcome_new_user').first()
        if welcome:
            wc = json.loads(welcome.value).get('html')
        else:
            wc = None

        self.render( 'home/welcome.html',
                     WELCOME = wc )



from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])

class Preview(RequestHandler):

    def post(self):
        markup_language = self.get_argument('markup_language', 'markdown')
        data = self.get_argument('data', None)

        d = { 'title': _('YLinux preview system'),
              'MARKUP': markup_language, 'BODY': '' }

        if data:
            if markup_language == 'markdown':
                d['BODY'] = YMK.convert(data)

        self.render('forum/topic/preview.html', **d)


class Search(RequestHandler):

    def get(self):
        d = {'title': _('Site Search')}
        self.render('home/search.html', **d)
