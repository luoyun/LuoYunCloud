# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission

from lycustom import has_permission


class PermissionManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.permission = None
        self.action = self.get_argument('action', 'index')

        permission_id = self.get_argument('id', 0)
        if permission_id:
            self.permission = self.db2.query(Permission).get( permission_id  )
            if not self.permission:
                self.write( _('No such permission : %s') % permission_id )
                return self.finish()


    def get(self):

        if self.action == 'index':
            if self.permission:
                self.get_view()
            else:
                self.get_index()

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):

        PERMISSION_LIST = self.db2.query(Permission).all()
        self.render( 'admin/permission/index.html', title = _('Permission Management'),
                     PERMISSION_LIST = PERMISSION_LIST )


    def get_view(self):

        self.render( 'admin/permission/view.html',
                     title = _("View Permission %s") % self.permission.name,
                     PERMISSION = self.permission )
                     
