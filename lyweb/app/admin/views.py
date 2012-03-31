# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from settings import JOB_ACTION, JOB_TARGET



class Index(LyRequestHandler):

    @authenticated
    def get(self):

        if self.current_user.id not in [ 1 ]:
            return self.write( _('No permissions !') )

        d = { 'title': 'Admin Console' }

        self.render('admin/index.html', **d)



class User(LyRequestHandler):


    @authenticated
    def get(self):

        if self.current_user.id not in [ 1 ]:
            return self.write( _('No permissions !') )

        USER_LIST = self.db.query("SELECT * FROM auth_user;")

        d = { 'title': _('User Management'),
              'USER_LIST': USER_LIST }

        self.render('admin/user.html', **d)



class Appliance(LyRequestHandler):


    @authenticated
    def get(self):

        if self.current_user.id not in [ 1 ]:
            self.write( _('No permissions !') )
            return self.finished()

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




class Instance(LyRequestHandler):


    @authenticated
    def get(self):

        if self.current_user.id not in [ 1 ]:
            return self.write( _('No permissions !') )

        by = self.get_argument('by', 'created')
        sort = self.get_argument('sort', 'DESC')
        page_size = int(self.get_argument('sepa', 10))
        cur_page = int(self.get_argument('p', 1))

        # TODO: no SQL-injection
        if not ( sort in ['DESC', 'ASC'] and
                 by  in ['updated', 'created'] ):
            return self.write(u'wrong URL !')

        offset = (cur_page - 1) * page_size

        SQL = "\
SELECT id, name, summary, logo, cpus, memory, user_id, \
       appliance_id, node_id, ip, status, created, updated \
FROM instance \
ORDER BY %s %s \
LIMIT %s OFFSET %s;" % (by, sort, page_size, offset)

        INSTANCE_LIST = self.db.query(SQL)

        TOTAL_INSTANCE = len( self.db.query(
                'SELECT id FROM instance;') )

        for I in INSTANCE_LIST:
            I.user = self.db.get('SELECT id, username \
FROM auth_user WHERE id=%s;', I.user_id )

        page_html = Pagination(
            total = TOTAL_INSTANCE,
            page_size = page_size,
            cur_page = cur_page ).html(self.get_page_url)


        d = { 'title': _('Instance'),
              'TOTAL_INSTANCE': TOTAL_INSTANCE,
              'INSTANCE_LIST': INSTANCE_LIST,
              'page_html': page_html,
              'cur_page': cur_page,
              'instance_status': self.instance_status,
              'instance_logo_url': self.instance_logo_url }
                              
        self.render('admin/instance.html', **d)



class ControlAllInstance(LyRequestHandler):
    ''' stop/start all instance '''

    @authenticated
    def get(self, action):

        if self.current_user.id not in [ 1 ]:
            return self.write( _('No permissions !') )

        if action == 'stop_all':
            action = 'stop'
            INSTANCE_LIST = self.db.query( 'SELECT id,status \
FROM instance WHERE status != 2;' )

        elif action == 'start_all':
            action = 'run'
            INSTANCE_LIST = self.db.query( 'SELECT id,status \
FROM instance WHERE status=2;' )

        else:
            return self.write( _('Unknown action "%s" !') % action )

        LYJOB_ACTION = self.settings['LYJOB_ACTION']
        action_id = LYJOB_ACTION.get(action, 0)

        JID_LIST = []

        for I in INSTANCE_LIST:
            jid = self.new_job(JOB_TARGET['INSTANCE'], I.id, action_id)
            JID_LIST.append(jid)

        self.write( _('%s all instance success: %s') % ( action, JID_LIST ) )
