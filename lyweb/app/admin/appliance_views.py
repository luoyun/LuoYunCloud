# coding: utf-8

import logging, datetime, time, re
from lycustom import RequestHandler
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc
from app.auth.models import User, Group, Permission
from app.appliance.models import Appliance, ApplianceCatalog

from app.admin.forms import ApplianceCatalogEditForm, \
    ApplianceEditForm

from lycustom import has_permission
from lytool.filesize import size as human_size
from ytool.pagination import pagination

from settings import LY_TARGET



class Index(RequestHandler):

    @has_permission('admin')
    def get(self):

        catalog_id = self.get_argument_int('catalog', 0)
        page_size = self.get_argument_int('sepa', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')
        uid = self.get_argument('uid', 0)

        if by not in [ 'name', 'created', 'updated', 'id', 'os',
                       'disksize',
                       'user_id', 'catalog_id', 'filesize',
                       'islocked', 'isprivate',
                       'like', 'unlike', 'visit' ]:
            by = 'id'

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        catalog = self.db.query(ApplianceCatalog).get( catalog_id )
        user = self.db.query(User).get( uid )

        apps = self.db.query(Appliance)

        if catalog:
            apps = apps.filter_by(catalog_id=catalog_id)

        if user:
            apps = apps.filter_by(user_id = uid)

        apps = apps.order_by(by_exp)

        total = apps.count()
        apps = apps.slice(start, stop)
            
        page_html = pagination(self.request.uri, total, page_size, cur_page)

        catalogs = self.db.query(ApplianceCatalog).all()
        for c in catalogs:
            c.total = self.db.query(Appliance.id).filter_by( catalog_id = c.id ).count()

        d = { 'title': _('LuoYun Appliance Management'),
              'BY': by, 'SORT': sort,
              'CATALOG_LIST': catalogs, 'CATALOG': catalog,
              'APPLIANCE_LIST': apps, 'PAGE_HTML': page_html,
              'CATALOG': catalog, 'USER': user,
              'TOTAL_APPLIANCE': total,
              'human_size': human_size,
              'urlupdate': self.urlupdate,
              'PAGE_SIZE': page_size }

        self.render( 'admin/appliance/index.html', **d )



class ApplianceView(RequestHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me appliance id please.') )

        A = self.db.query(Appliance).get( ID )
        if not A:
            return self.write( _('Can not find appliance %s') % ID )

        self.render( 'admin/appliance/view.html',
                     title = _('View Appliance "%s"') % A.name,
                     APPLIANCE = A,
                     human_size = human_size )



class ApplianceChangeUser(RequestHandler):

    title = _('Change owner of appliance')
    template_path = 'admin/appliance/change_owner.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give me appliance id please.') )

        A = self.db.query(Appliance).get( ID )
        if not A:
            return self.finish( _('Can not find appliance %s') % ID )

        self.prepare_kwargs['APPLIANCE'] = A


    def get(self):
        self.render()

    def post(self):

        A = self.prepare_kwargs['APPLIANCE']
        E = []
        U = None

        user = self.get_argument('user', 0)
        if user:
            if user.isdigit():
                U = self.db.query(User).get(user)

            if not U:
                U = self.db.query(User).filter_by(
                    username = user ).first()

            if U:

                old_owner = A.user.username
                new_owner = U.username

                A.user = U
                self.db.commit()

                # save trace
                do = _('change owner %(old)s to %(new)s') % {
                    'old': old_owner, 'new': new_owner }

                reason = self.get_argument('reason', None)
                if reason:
                    do += ' : %s' % reason

                T = self.lytrace( ttype = LY_TARGET['APPLIANCE'],
                                  tid = A.id, do = do )

                # TODO: send reason to user
                url = self.reverse_url('admin:appliance:view')
                url += '?id=%s' % A.id
                return self.redirect( url )

            else:
                E.append( _('Can not find user %s') % user )
        else:
            E.append( _('No user input !') )

        self.render(ERROR = E)



class ApplianceEdit(RequestHandler):

    title = _('Edit Appliance')
    template_path = 'admin/appliance/edit.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give me appliance id please.') )

        A = self.db.query(Appliance).get( ID )
        if not A:
            return self.finish( _('Can not find appliance %s') % ID )


        catalog_choices = []
        for s in self.db.query(ApplianceCatalog.id,
                               ApplianceCatalog.name).all():
            catalog_choices.append( (str(s.id), s.name) )

        form = ApplianceEditForm(self)
        form.catalog.choices = catalog_choices

        self.prepare_kwargs['APPLIANCE'] = A
        self.prepare_kwargs['form'] = form


    def get(self):

        A = self.prepare_kwargs['APPLIANCE']
        form = self.prepare_kwargs['form']

        form.catalog.default = A.catalog_id
        form.os.default = A.os
        form.process()

        form.name.data = A.name
        form.summary.data = A.summary
        form.description.data = A.description

        self.render()

    def post(self):

        A = self.prepare_kwargs['APPLIANCE']
        form = self.prepare_kwargs['form']

        if form.validate():
            A.name        = form.name.data
            A.os          = self.get_int(form.os.data)
            A.summary     = form.summary.data
            A.catalog_id  = form.catalog.data
            A.description = form.description.data

            # Save logo file
            if self.request.files:
                r = A.save_logo(self.request.files['logo'])
                if r:
                    form.logo.errors.append( r )

            self.db.commit()
            url = self.reverse_url('admin:appliance:view')
            url += '?id=%s' % A.id
            return self.redirect( url )


        self.render()



class CatalogIndex(RequestHandler):

    @has_permission('admin')
    def get(self):

        CL = self.db.query(ApplianceCatalog).order_by('id').all()

        d = { 'title': _('Appliance Catalog Home'),
              'CATALOG_LIST': CL }

        self.render( 'admin/appliance/catalog/index.html', **d )



class CatalogView(RequestHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me catalog id please.') )

        C = self.db.query(ApplianceCatalog).get( ID )
        if not C:
            return self.write( _('Can not find catalog %s') % ID )


        d = { 'title': _('View Appliance Catalog : "%s"') % C.name,
              'CATALOG': C }

        self.render( 'admin/appliance/catalog/view.html', **d )



class CatalogAdd(RequestHandler):

    title = _('Add Appliance Catalog')
    template_path = 'admin/appliance/catalog/add.html'

    @has_permission('admin')
    def prepare(self):
        self.prepare_kwargs['form'] = ApplianceCatalogEditForm(self)

    def get(self):
        self.render()

    def post(self):

        form = self.prepare_kwargs['form']

        if form.validate():
            C = ApplianceCatalog(
                name        = form.name.data,
                summary     = form.summary.data,
                description = form.description.data )
            self.db.add( C )
            self.db.commit()

            url = self.reverse_url('admin:appliance:catalog:view')
            url += '?id=%s' % C.id
            return self.redirect( url )

        self.render()


class CatalogEdit(RequestHandler):

    title = _('Edit Appliance Catalog')
    template_path = 'admin/appliance/catalog/edit.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give me catalog id please.') )

        C = self.db.query(ApplianceCatalog).get( ID )
        if not C:
            return self.finish( _('Can not find catalog %s') % ID )

        self.prepare_kwargs['form'] = ApplianceCatalogEditForm(self)
        self.prepare_kwargs['CATALOG'] = C


    def get(self):

        C = self.prepare_kwargs['CATALOG']
        form = self.prepare_kwargs['form']

        form.name.data        = C.name
        form.summary.data     = C.summary
        form.description.data = C.description

        self.render()


    def post(self):

        C = self.prepare_kwargs['CATALOG']
        form = self.prepare_kwargs['form']

        if form.validate():
            C.name        = form.name.data
            C.summary     = form.summary.data
            C.description = form.description.data
            self.db.commit()

            url = self.reverse_url('admin:appliance:catalog:view')
            url += '?id=%s' % C.id
            return self.redirect( url )

        self.render()



class CatalogDelete(RequestHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me catalog id please.') )

        C = self.db.query(ApplianceCatalog).get( ID )
        if not C:
            return self.write( _('Can not find catalog %s') % ID )

        if len(C.appliances):
            return self.write( _('There are appliances exist, can not delete catalog now.') )

        self.db.delete( C )
        self.db.commit()

        url = self.reverse_url('admin:appliance:catalog')
        self.redirect( url )




class ApplianceManagement(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.appliance = None
        self.action = self.get_argument('action', 'index')

        appliance_id = self.get_argument('id', 0)
        if appliance_id:
            self.appliance = self.db.query(Appliance).get( appliance_id )
            if not self.appliance:
                self.write( self.trans(_('No such appliance : %s')) % appliance_id )
                return self.finish()

        c_id = self.get_argument('catalog', 0)
        self.catalog = self.db.query(ApplianceCatalog).get(c_id)


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
            self.write( self.trans(_('Wrong action value!')) )


    def post(self):

        if not self.action:
            self.write( self.trans(_('No action found !')) )

        elif self.action == 'change_owner':
            self.change_owner()

        elif self.action == 'change_catalog':
            self.change_catalog()

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def change_catalog(self):

        CATALOG_LIST = self.db.query(ApplianceCatalog).all()

        d = { 'title': self.trans(_('Change catalog of appliance')),
              'A': self.appliance, 'CATALOG_LIST': CATALOG_LIST }

        E = []
        U = None
        
        if self.request.method == 'POST':
            cid = self.get_argument('catalog', 0)
            if cid:
                C = self.db.query(ApplianceCatalog).get(cid)
                if not C:
                    E.append( self.trans(_('Can not find catalog %s')) % cid )
            else:
                E.append( self.trans(_('No catalog input !')) )

            if E:
                d['ERROR'] = E
            else:
                self.appliance.catalog = C
                self.db.commit()

                url = self.reverse_url('admin:appliance')
                url += '?id=%s' % self.appliance.id
                return self.redirect( url )

        self.render( 'admin/appliance/change_catalog.html', **d)




