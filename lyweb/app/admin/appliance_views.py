# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc
from app.account.models import User, Group, Permission
from app.appliance.models import Appliance, ApplianceCatalog

from app.admin.forms import CatalogForm

from lycustom import has_permission


class ApplianceManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.appliance = None
        self.action = self.get_argument('action', 'index')

        appliance_id = self.get_argument('id', 0)
        if appliance_id:
            self.appliance = self.db2.query(Appliance).get( appliance_id )
            if not self.appliance:
                self.write( _('No such appliance : %s') % appliance_id )
                return self.finished()

        c_id = self.get_argument('catalog', 0)
        self.catalog = self.db2.query(ApplianceCatalog).get(c_id)



    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'appliances':
            self.get_appliances()

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
        catalogs = self.db2.query(ApplianceCatalog).all()
        self.render( 'admin/appliance/index.html',
                     title = _('Appliance Management'),
                     catalogs = catalogs )


    def get_appliances(self):

        by = self.get_argument('by', 'id')
        order = self.get_argument('order', 'asc')
        if order == 'asc':
            order_func = asc(by)
        else:
            order_func = desc(by)

        apps = self.db2.query(Appliance).order_by(order_func)

        if self.catalog:
            apps = apps.filter_by(catalog_id=self.catalog.id).order_by( order_func )

        self.render( 'admin/appliance/appliances.html',
                     title = _('List appliances'),
                     APPLIANCE_LIST = apps,
                     catalog = self.catalog )



    def get_add_catalog(self):

        form = CatalogForm()

        self.render( 'admin/appliance/add_catalog.html',
                     title = _('Add Appliance Catalog'),
                     form = form )


    def post_add_catalog(self):

        form = CatalogForm( self.request.arguments )
        if form.validate():
            c = ApplianceCatalog( name = form.name.data,
                                  summary = form.summary.data,
                                  description = form.description.data )
            self.db2.add( c )
            self.db2.commit()

            url = self.reverse_url('admin:appliance')
            return self.redirect( url )

        self.render( 'admin/appliance/add_catalog.html',
                     title = _('Add Appliance Catalog'),
                     form = form )


    def get_edit_catalog(self):

        if not self.catalog:
            return self.write( _('No catalog found') )
        
        form = CatalogForm()
        form.name.data = self.catalog.name
        form.summary.data = self.catalog.summary
        form.description.data = self.catalog.description

        self.render( 'admin/appliance/edit_catalog.html',
                     title = _('Edit appliance catalog: %s') % self.catalog.name,
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

            url = self.reverse_url('admin:appliance')
            return self.redirect( url )

        self.render( 'admin/appliance/add_catalog.html',
                     title = _('Add Appliance Catalog'),
                     form = form )
