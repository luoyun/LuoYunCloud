# coding: utf-8

import logging, datetime, time, re
from lycustom import RequestHandler
from tornado.web import authenticated, asynchronous

from app.auth.models import User, Group, Permission

from lycustom import has_permission


class PermissionManagement(RequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.permission = None
        self.action = self.get_argument('action', 'index')

        permission_id = self.get_argument('id', 0)
        if permission_id:
            self.permission = self.db.query(Permission).get( permission_id  )
            if not self.permission:
                self.write( self.trans(_('No such permission : %s')) % permission_id )
                return self.finish()


    def get(self):

        PERMISSION_LIST = self.db.query(Permission).all()
        self.render( 'admin/permission/index.html', title = self.trans(_('Permission Management')),
                     PERMISSION_LIST = PERMISSION_LIST )
