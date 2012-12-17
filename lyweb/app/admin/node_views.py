# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.node.models import Node
from app.instance.models import Instance

from sqlalchemy.sql.expression import asc, desc

from lycustom import has_permission
import settings


class NodeManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.node = None
        self.action = self.get_argument('action', 'index')

        node_id = self.get_argument('id', 0)
        if node_id:
            self.node = self.db2.query(Node).get( node_id )
            if not self.node:
                self.write( self.trans(_('No such node')) % node_id )
                return self.finish()
            else:
                self.action = 'view'


    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'view':
            self.get_view()

        elif self.action == 'instances':
            self.get_instances()

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def post(self):

        if not self.action:
            self.write( self.trans(_('No action found !')) )

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def get_index(self):

        nodes = self.db2.query(Node).order_by(asc(Node.id)).all()
        run_status = settings.INSTANCE_SLIST_RUNING
        for N in nodes:
            il = self.db2.query(Instance.id).filter(
                Instance.node_id == N.id )
            N.instances_sum = il.count()
            N.instances_running_sum = il.filter(
                Instance.status.in_( run_status ) ).count()

        self.render( 'admin/node/index.html', title = self.trans(_('Node Management')),
                     nodes = nodes )


    def get_view(self):

        d = { 'NODE': self.node }
        self.render( 'admin/node/view.html', **d )


    def get_instances(self):

        instances = self.db2.query(Instance).filter(
            Instance.node_id == self.node.id
            ).order_by('id').all()

        self.render( 'admin/node/instances.html',
                     NODE=self.node,
                     INSTANCE_LIST = instances )
