# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous



class Index(LyRequestHandler):

    @authenticated
    def get(self):

        if self.current_user.id not in [ 1 ]:
            return self.write( _('No permissions !') )

        d = { 'title': 'Admin Console' }

        self.render('admin/index.html', **d)



class Appliance(LyRequestHandler):

    @authenticated
    def prepare(self):

        if self.current_user.id not in [ 1 ]:
            self.write( _('No permissions !') )
            return self.finished()


    def get(self):

        c = int( self.get_argument('c', 1) )

        catalogs = self.db.query(
            'SELECT id, name FROM appliance_catalog;' )


        CATALOG = self.db.get(
            "SELECT * FROM appliance_catalog WHERE id=%s;", c)


        d = { 'title': _('Appliance Management'),
              'catalogs': catalogs,
              'CATALOG': CATALOG,
              'cur_catalog': c }

        self.render('admin/appliance.html', **d)



class ApplianceAddCatalog(LyRequestHandler):

    #''' Add/Edit/Delete Catalog of appliance '''

    def initialize(self):
        self.t = 'admin/appliance_add_catalog.html'
        self.d = { 'title': _('Add Appliance Catalog') }


    @authenticated
    def prepare(self):

        if self.current_user.id not in [ 1 ]:
            self.write( _('No permissions !') )
            return self.finished()


    def get(self):

        self.render( self.t, **self.d )


    def post(self):

        d = self.d

        d['name'] = self.get_argument('name', '')
        d['summary'] = self.get_argument('summary', '')
        d['description'] = self.get_argument('description', '')

        if not d['name']:
            d['name_error'] = _('Name is required !')
            return self.render( self.t, **d )

        try:
            self.db.execute(
                "INSERT INTO appliance_catalog \
(name, summary, description, created, updated) \
VALUES (%s, %s, %s, 'now', 'now');",
                d['name'], d['summary'], d['description'] )

        except Exception, emsg:
            return self.write(
                _('Add catalog to DB failed: %s') % emsg )

        self.redirect('/admin')



class ApplianceEditCatalog(LyRequestHandler):


    def initialize(self):
        self.t = 'admin/appliance_edit_catalog.html'
        self.d = { 'title': _('Edit Appliance Catalog') }


    @authenticated
    def prepare(self):

        id = re.match('.*/([0-9]+)/.*',
                      self.request.path).groups()[0]
        c = self.db.get(
            'SELECT * FROM appliance_catalog WHERE id=%s;',
            id )

        if not c:
            self.write(u'No catalog %s !' % id)
            return self.finish()

        if self.current_user.id not in [ 1 ]:
            self.write( _('No permissions !') )
            return self.finished()

        self.d['name'] = c.name
        self.d['summary'] = c.summary
        self.d['description'] = c.description


    def get(self, id):

        self.render( self.t, **self.d )


    def post(self, id):

        d = self.d

        d['name'] = self.get_argument('name', '')
        d['summary'] = self.get_argument('summary', '')
        d['description'] = self.get_argument('description', '')

        if not d['name']:
            d['name_error'] = _('Name is required !')
            return self.render( self.t, **d )

        try:
            self.db.execute(
                "UPDATE appliance_catalog SET \
name=%s, summary=%s, description=%s, updated='now' \
WHERE id=%s;",
                d['name'], d['summary'], d['description'],
                id )

        except Exception, emsg:
            return self.write( 'DB error: %s' % emsg )

        self.redirect('/admin/appliance?c=%s' % id)
        



class Wiki(LyRequestHandler):

    @authenticated
    def prepare(self):

        if self.current_user.id not in [ 1 ]:
            self.write( _('No permissions !') )
            return self.finished()


    def get(self):

        c = int( self.get_argument('c', 1) )

        catalogs = self.db.query(
            'SELECT id, name FROM wiki_catalog;' )


        CATALOG = self.db.get(
            "SELECT * FROM wiki_catalog WHERE id=%s;", c)


        d = { 'title': _('Wiki Management'),
              'catalogs': catalogs,
              'CATALOG': CATALOG,
              'cur_catalog': c }

        self.render('admin/wiki.html', **d)


class WikiAddCatalog(LyRequestHandler):

    @authenticated
    def prepare(self):
        self.d = { 'title': 'Add catalog', 'ERROR': [] }
        self.t = 'admin/wiki_add_catalog.html'


    def get(self):

        if self.current_user.id not in [1]:
            self.write(u'No permission to create catalog !')
        else:
            self.render(self.t, **self.d)


    def post(self):

        d = self.d

        d['name'] = self.get_argument('name', '')
        d['summary'] = self.get_argument('summary', '')
        d['description'] = self.get_argument('description', '')
        if not d['name']:
            d['ERROR'].append = 'Name is required !'
            return self.render(self.t, **d)

        try:
            self.db.execute(
                "INSERT INTO wiki_catalog (name, summary, \
description, created, updated) VALUES (\
%s, %s, %s, 'now', 'now');",
                d['name'], d['summary'], d['description'] )
        except Exception, emsg:
            return self.write('DB error: %s' % emsg)

        self.redirect('/admin/wiki')




class WikiEditCatalog(LyRequestHandler):


    def initialize(self):

        self.d = { 'title': 'Edit catalog', 'ERROR': [] }
        self.t = 'admin/wiki_edit_catalog.html'


    @authenticated
    def prepare(self):

        id = re.match('.*/([0-9]+)/.*',
                      self.request.path).groups()[0]
        c = self.db.get(
            'SELECT * FROM wiki_catalog WHERE id=%s;', id )

        if not c:
            self.write(u'No catalog %s !' % id)
            return self.finish()

        if self.current_user.id not in [1]:
            self.write('No permissions !')
            return self.finish()

        self.d['name'] = c.name
        self.d['summary'] = c.summary
        self.d['description'] = c.description


    def get(self, id):

        self.render(self.t, **self.d)


    def post(self, id):

        d = self.d

        name = self.get_argument('name', '')
        summary = self.get_argument('summary', '')
        description = self.get_argument('description', '')

        d['name'] = name
        d['summary'] = summary
        d['description'] = description

        if not name:
            d['ERROR'].append = 'Name is required !'
            return self.render(self.t, **d)

        try:
            self.db.execute(
                "UPDATE wiki_catalog SET \
name=%s, summary=%s, description=%s, updated='now' \
WHERE id=%s;",
                name, summary, description, id )

        except Exception, emsg:
            return self.write('DB error: %s' % emsg)

        self.redirect('/admin/wiki?c=%s' % id)
