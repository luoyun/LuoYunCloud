# coding: utf-8

import os, datetime, random, time, re
import tornado
from tornado.web import authenticated
from sqlalchemy.sql.expression import asc, desc, func

from ..auth.models import User
from lycustom import RequestHandler, has_permission

from .models import ForumCatalog, ForumTopic, ForumPost, \
    ForumTopicTag
from .forms import TopicForm, PostForm, \
    CatalogForm

from ytool.pagination import pagination



class Index(RequestHandler):

    @has_permission('admin')
    def get(self):

        CATALOG_TOTAL = self.db.query(ForumCatalog.id).count()
        TOPIC_TOTAL = self.db.query(ForumTopic.id).count()
        TAG_TOTAL = self.db.query(ForumTopicTag.id).count()

        d = { 'title': _('Forum Management'),
              'CATALOG_TOTAL': CATALOG_TOTAL,
              'TOPIC_TOTAL': TOPIC_TOTAL,
              'TAG_TOTAL': TAG_TOTAL }

        self.render('admin/forum/index.html', **d)



class CatalogIndex(RequestHandler):

    @has_permission('admin')
    def get(self):

        CID = self.get_argument_int('id', None)
        if CID:
            CUR_CATALOG = self.db.query(ForumCatalog).get( CID )
            CATALOGS = self.db.query(ForumCatalog).filter_by(
                parent_id = CID).all()
        else:
            CUR_CATALOG = None
            CATALOGS = self.db.query(ForumCatalog).filter_by(
                parent_id = None).all()


        d = { 'title': _('Forum Catalog'),
              'CATALOG_LIST': CATALOGS,
              'CUR_CATALOG': CUR_CATALOG }

        self.render('admin/forum/catalog.html', **d)



class CatalogAdd(RequestHandler):

    title = _('Add Forum Catalog')
    template_path = 'admin/forum/catalog_edit.html'

    @has_permission('admin')
    def prepare(self):

        self.P_CATALOG = None

        PID = self.get_argument_int('pid', None)
        if PID:
            self.P_CATALOG = self.db.query(ForumCatalog).get( PID )

        self.prepare_kwargs['P_CATALOG'] = self.P_CATALOG
        self.prepare_kwargs['form'] = CatalogForm(self)

    def get(self):
        self.render()

    def post(self):

        form = self.prepare_kwargs['form']

        if form.validate():

            c = ForumCatalog( name        = form.name.data,
                              summary     = form.summary.data,
                              description = form.description.data )

            if self.P_CATALOG:
                c.parent_id = self.P_CATALOG.id

            self.db.add( c )
            self.db.commit()

            url = self.reverse_url('admin:forum:catalog')
            return self.redirect( url )

        self.render()
