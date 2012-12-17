# coding: utf-8

import logging, struct, socket, re, os, json, ConfigParser
import ConfigParser

from tornado.web import RequestHandler, authenticated, asynchronous

import mako
from mako.template import Template
from mako.lookup import TemplateLookup
mako.runtime.UNDEFINED = ''

from app.install.forms import BaseForm

import settings


class InstallRequestHandler(RequestHandler):

    lookup = TemplateLookup([ settings.TEMPLATE_DIR ],
                            input_encoding="utf-8")

    def render(self, template_name, **kwargs):
        """ Redefine the render """

        # TODO: if url have ajax arg, use XXX.ajax for template
        if self.get_argument('ajax', False):
            x, y = template_name.split('.')
            #x += '_ajax'
            template_name = '.'.join([x,'ajax'])

        t = self.lookup.get_template(template_name)

        args = dict(
            handler=self,
            request=self.request,
            current_user=self.current_user,
            locale=self.locale,
            _=self.locale.translate,
            static_url=self.static_url,
            xsrf_form_html=self.xsrf_form_html,
            reverse_url=self.application.reverse_url,

            LANGUAGES=self.settings['LANGUAGES'],
            STATIC_URL=self.settings['STATIC_URL'],
            THEME_URL=self.settings['THEME_URL'],
        )

        args.update(kwargs)

        # We can define keyword in views with initialize()
        if hasattr(self, 'view_kwargs'):
            args.update(self.view_kwargs)

        html = t.render(**args)
        self.finish(html)



class Index(InstallRequestHandler):

    def prepare(self):

        self.cf = ConfigParser.ConfigParser()
        self.cf.read( settings.LUOYUN_CONFIG_PATH )
        if not self.cf.has_section('db'):
            self.cf.add_section('db')


    def get(self):

        cf = self.cf
        form = BaseForm(self)
        try:
            form.dbname.data = cf.get('db', 'db_name')
            form.dbuser.data = cf.get('db', 'db_user')
            form.dbpass.data = cf.get('db', 'db_password')
            form.dbhost.data = cf.get('db', 'db_host')
            form.dbtype.data = cf.get('db', 'db_type')
        except:
            pass

        self.render('install/index.html', form=form)


    def post(self):

        cf = self.cf
        saved = None

        form = BaseForm(self)
        if form.validate():
            cf.set('db', 'db_host', form.dbhost.data)
            cf.set('db', 'db_type', form.dbtype.data)
            cf.set('db', 'db_name', form.dbname.data)
            cf.set('db', 'db_user', form.dbuser.data)
            cf.set('db', 'db_password', form.dbpass.data)
            cf.write(open(settings.LUOYUN_CONFIG_PATH, 'w'))

            saved = True
            # TODO: Important ! db settings should check for connect !

        self.render('install/index.html', form=form, saved = saved)



class Reload(InstallRequestHandler):

    def get(self):
        # TODO: restart program
        from settings import restart_luoyun_web
        restart_luoyun_web()

