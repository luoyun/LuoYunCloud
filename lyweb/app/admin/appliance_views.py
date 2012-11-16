# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc
from app.account.models import User, Group, Permission
from app.appliance.models import Appliance, ApplianceCatalog

from app.admin.forms import CatalogForm

from lycustom import has_permission
from lytool.filesize import size as human_size

from settings import LY_TARGET

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
                return self.finish()

        c_id = self.get_argument('catalog', 0)
        self.catalog = self.db2.query(ApplianceCatalog).get(c_id)


    def get(self):

        if self.action == 'index':
            if self.appliance:
                self.get_view()
            else:
                self.get_index()

        elif self.action == 'change_owner':
            self.change_owner()

        elif self.action == 'change_catalog':
            self.change_catalog()

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        elif self.action == 'change_owner':
            self.change_owner()

        elif self.action == 'change_catalog':
            self.change_catalog()

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):

        catalog_id = self.catalog.id if self.catalog else 0
        page_size = self.get_argument_int('sepa', 10)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')
        uid = self.get_argument('uid', 0)

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        catalog = self.db2.query(ApplianceCatalog).get( catalog_id )
        user = self.db2.query(User).get( uid )

        apps = self.db2.query(Appliance)

        if catalog:
            apps = apps.filter_by(catalog_id=catalog_id)

        if user:
            apps = apps.filter_by(user_id = uid)

        apps = apps.order_by(by_exp)

        total = apps.count()
        apps = apps.slice(start, stop)
            
        pagination = Pagination(
            total = total,
            page_size = page_size, cur_page = cur_page )

        page_html = pagination.html( self.get_page_url )

        catalogs = self.db2.query(ApplianceCatalog).all()
        for c in catalogs:
            c.total = self.db2.query(Appliance.id).filter_by( catalog_id = c.id ).count()

        d = { 'title': _('LuoYun Appliance Management'),
              'CATALOG_LIST': catalogs, 'CID': catalog_id,
              'APPLIANCE_LIST': apps, 'PAGE_HTML': page_html,
              'CATALOG': catalog, 'USER': user,
              'TOTAL_APPLIANCE': total,
              'human_size': human_size }

        self.render( 'admin/appliance/index.html', **d )



    def get_view(self):
        catalogs = self.db2.query(ApplianceCatalog).all()
        self.render( 'admin/appliance/view.html',
                     title = _('View Appliance %s') % self.appliance.name,
                     CATALOG_LIST = catalogs,
                     APPLIANCE = self.appliance,
                     human_size = human_size )

    def change_owner(self):
        d = { 'title': _('Change owner of appliance'),
              'A': self.appliance }
        
        E = []
        U = None
        
        if self.request.method == 'POST':
            user = self.get_argument('user', 0)
            if user:
                if user.isdigit():
                    U = self.db2.query(User).get(user)
                if not U:
                    U = self.db2.query(User).filter_by(username=user).first()
                if not U:
                    E.append( _('Can not find user: %s') % user )
            else:
                E.append( _('No user input !') )

            reason = self.get_argument('reason', '')

            if E:
                d['ERROR'] = E
            else:
                T = self.lytrace(
                    ttype = LY_TARGET['APPLIANCE'],
                    tid = self.appliance.id,
                    do = _('change appliance owner %s to %s') % (
                        self.appliance.user.username, U.username) )

                self.appliance.user = U
                self.db2.commit()

                # TODO: send reason to user
                url = self.reverse_url('admin:appliance')
                url += '?id=%s' % self.appliance.id
                return self.redirect( url )

        self.render( 'admin/appliance/change_owner.html', **d)


    def change_catalog(self):

        CATALOG_LIST = self.db2.query(ApplianceCatalog).all()

        d = { 'title': _('Change catalog of appliance'),
              'A': self.appliance, 'CATALOG_LIST': CATALOG_LIST }

        E = []
        U = None
        
        if self.request.method == 'POST':
            cid = self.get_argument('catalog', 0)
            if cid:
                C = self.db2.query(ApplianceCatalog).get(cid)
                if not C:
                    E.append( _('Can not find catalog %s') % cid )
            else:
                E.append( _('No catalog input !') )

            if E:
                d['ERROR'] = E
            else:
                self.appliance.catalog = C
                self.db2.commit()

                url = self.reverse_url('admin:appliance')
                url += '?id=%s' % self.appliance.id
                return self.redirect( url )

        self.render( 'admin/appliance/change_catalog.html', **d)




class CatalogManagement(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.action = self.get_argument('action', 'index')

        cid = self.get_argument_int('id', 0)
        self.catalog = self.db2.query(ApplianceCatalog).get(cid)

        if self.action in ['edit'] and not self.catalog:
            self.write( _('No catalog specified !') )
            return self.finish()


    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'new':
            self.get_new()

        elif self.action == 'edit':
            self.get_edit()

        else:
            self.write( _('Wrong action: %s') % self.action )


    def post(self):

        if self.action == 'new':
            self.post_new()

        elif self.action == 'edit':
            self.post_edit()

        else:
            self.write( _('Wrong action: %s') % self.action )


    def get_index(self):

        CL = self.db2.query(ApplianceCatalog).order_by('id').all()

        d = { 'title': _('Appliance Catalog'),
              'CATALOG_LIST': CL }

        self.render( 'admin/appliance/catalog.html', **d )


    def get_new(self):
        self.render( 'admin/appliance/catalog_new.html',
                     title = _('Add Appliance Catalog'),
                     form = CatalogForm() )

    def post_new(self):

        form = CatalogForm( self.request.arguments )
        if form.validate():
            c = ApplianceCatalog(
                name = form.name.data,
                summary = form.summary.data,
                description = form.description.data )
            self.db2.add( c )
            self.db2.commit()

            url = self.reverse_url('admin:appliance:catalog')
            return self.redirect( url )

        self.render( 'admin/appliance/catalog_new.html',
                     title = _('Add Appliance Catalog'),
                     form = form )


    def get_edit(self):

        form = CatalogForm()
        form.name.data = self.catalog.name
        form.summary.data = self.catalog.summary
        form.description.data = self.catalog.description

        self.render( 'admin/appliance/catalog_edit.html',
                     title = _('Edit Appliance Catalog: %s') % self.catalog.name,
                     form = form )


    def post_edit(self):

        form = CatalogForm( self.request.arguments )
        if form.validate():
            self.catalog.name = form.name.data
            self.catalog.summary = form.summary.data
            self.catalog.description = form.description.data
            self.db2.commit()

            url = self.reverse_url('admin:appliance:catalog')
            return self.redirect( url )

        self.render( 'admin/appliance/catalog_edit.html',
                     title = _('Edit Appliance Catalog: %s') % self.catalog.name,
                     form = form )

