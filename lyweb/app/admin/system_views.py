# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission

from lycustom import has_permission


class SystemManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.action = self.get_argument('action', 'index')


    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'syncdb':
            self.get_syncdb()

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):

        self.render( 'admin/system/index.html', title = _('System Management') )


    def get_syncdb(self):

        from lyorm import ORMBase, dbengine
        ORMBase.metadata.create_all(dbengine)

        url = self.application.reverse_url('admin:system')
        return self.redirect( url )

