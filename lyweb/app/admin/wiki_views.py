# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.wiki.models import Topic, WikiCatalog

from app.admin.forms import CatalogForm

from lycustom import has_permission


class WikiManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.topic = None
        self.action = self.get_argument('action', 'index')

        topic_id = self.get_argument('id', 0)
        if topic_id:
            self.topic = self.db2.query(Topic).get( topic_id )
            if not self.topic:
                self.write( _('No such topic : %s') % topic_id )
                return self.finish()

        c_id = self.get_argument('catalog', 0)
        self.catalog = self.db2.query(WikiCatalog).get(c_id)



    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'topics':
            self.get_topics()

        elif self.action == 'add_catalog':
            self.get_add_catalog()

        elif self.action == 'edit_catalog':
            self.get_edit_catalog()

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        elif self.action == 'add_catalog':
            self.post_add_catalog()

        elif self.action == 'edit_catalog':
            self.post_edit_catalog()

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):
        catalogs = self.db2.query(WikiCatalog).all()
        self.render( 'admin/wiki/index.html',
                     title = _('Wiki Management'),
                     catalogs = catalogs )


    def get_topics(self):

        topics = self.db2.query(Topic)

        if self.catalog:
            topics = topics.filter_by(catalog_id=self.catalog.id)

        self.render( 'admin/wiki/topics.html',
                     title = _('List appliances'),
                     TOPIC_LIST = topics,
                     catalog = self.catalog )



    def get_add_catalog(self):

        form = CatalogForm()

        self.render( 'admin/wiki/add_catalog.html',
                     title = _('Add Wiki Catalog'),
                     form = form )


    def post_add_catalog(self):

        form = CatalogForm( self.request.arguments )
        if form.validate():
            c = WikiCatalog( name = form.name.data,
                             summary = form.summary.data,
                             description = form.description.data )
            self.db2.add( c )
            self.db2.commit()

            url = self.reverse_url('admin:wiki')
            return self.redirect( url )

        self.render( 'admin/wiki/add_catalog.html',
                     title = _('Add Wiki Catalog'),
                     form = form )


    def get_edit_catalog(self):

        if not self.catalog:
            return self.write( _('No catalog found') )
        
        form = CatalogForm()
        form.name.data = self.catalog.name
        form.summary.data = self.catalog.summary
        form.description.data = self.catalog.description

        self.render( 'admin/wiki/edit_catalog.html',
                     title = _('Edit catalog: %s') % self.catalog.name,
                     form = form )


    def post_edit_catalog(self):

        if not self.catalog:
            return self.write( _('No catalog found') )

        form = CatalogForm( self.request.arguments )
        if form.validate():
            self.catalog.name = form.name.data
            self.catalog.summary = form.summary.data
            self.catalog.description = form.description.data
            self.db2.commit()

            url = self.reverse_url('admin:wiki')
            return self.redirect( url )

        self.render( 'admin/wiki/add_catalog.html',
                     title = _('Edit Catalog'),
                     form = form )
