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
    CatalogForm, CatalogAddForm



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

        CATALOGS = self.db.query(ForumCatalog).filter_by(
            parent_id = None).all()


        d = { 'title': _('Forum Catalog'),
              'CATALOG_LIST': CATALOGS }

        self.render('admin/forum/catalog/index.html', **d)



class CatalogView(RequestHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me catalog id please') )

        C = self.db.query(ForumCatalog).get( ID )
        if not C:
            return self.write( _('Can not find catalog %s') % ID )

        CATALOGS = self.db.query(ForumCatalog).filter_by(
            parent_id = ID).all()

        d = { 'title': _('View Catalog "%s"') % C.name,
              'SUB_CATALOG_LIST': CATALOGS,
              'CATALOG': C }

        self.render('admin/forum/catalog/view.html', **d)



class CatalogAdd(RequestHandler):

    title = _('Add Forum Catalog')
    template_path = 'admin/forum/catalog/edit.html'

    @has_permission('admin')
    def prepare(self):

        self.P_CATALOG = None

        PID = self.get_argument_int('pid', None)
        if PID:
            self.P_CATALOG = self.db.query(ForumCatalog).get( PID )

        self.prepare_kwargs['P_CATALOG'] = self.P_CATALOG
        self.prepare_kwargs['form'] = CatalogAddForm(self)

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

            # Save logo file
            if self.request.files:
                c.save_logo(self.request.files['logo'])

            self.db.commit()

            url = self.reverse_url('admin:forum:catalog')
            return self.redirect( url )

        self.render()



class CatalogEdit(RequestHandler):

    title = _('Edit Forum Catalog')
    template_path = 'admin/forum/catalog/edit.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give me catalog id please') )

        C = self.db.query(ForumCatalog).get( ID )
        if not C:
            return self.finish( _('Can not find catalog %s') % ID )

        self.prepare_kwargs['CATALOG'] = C
        self.prepare_kwargs['form'] = CatalogForm(self)

    def get(self):

        C = self.prepare_kwargs['CATALOG']
        form = self.prepare_kwargs['form']

        form.name.data = C.name
        form.summary.data = C.summary
        form.description.data = C.description

        self.render()

    def post(self):

        form = self.prepare_kwargs['form']
        C = self.prepare_kwargs['CATALOG']

        if form.validate():

            C.name        = form.name.data
            C.summary     = form.summary.data
            C.description = form.description.data

            print 'here 10'
            # Save logo file
            if self.request.files:
                e = C.save_logo(self.request.files['logo'])
                print 'e = ', e

            self.db.commit()

            url = self.reverse_url('admin:forum:catalog:view')
            url += '?id=%s' % C.id
            return self.redirect( url )

        self.render()
