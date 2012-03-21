# coding: utf-8

import os, logging, re
import settings

from lycustom import LyRequestHandler, Pagination
from tornado.web import authenticated, HTTPError



class AppRequestHandler(LyRequestHandler):


    def initialize(self):

        self.view_kwargs = {
            'app_logo_url': self.app_logo_url,
            }


    def app_logo_url(self, app):

        if hasattr(app, 'logoname') and app.logoname:
            return '%s%s' % (
                self.settings['appliance_top_url'],
                app.logoname)
        else:
            return '%simg/appliance.png' % (
                self.settings['THEME_URL'] )

    def done(self, msg):

        ajax = int(self.get_argument('ajax', 0))

        if ajax:
            self.write(msg)
        else:
            self.render( 'appliance/action_result.html',
                         msg = msg )







class Index(AppRequestHandler):


    def get(self):

        catalog_id = int( self.get_argument('c', 1) )
        page_size = int( self.get_argument('sepa', 10) )
        cur_page = int( self.get_argument('p', 1) )
        by = self.get_argument('by', 'updated')
        sort = self.get_argument('sort', 'DESC')

        # TODO: no SQL-injection
        if not ( sort in ['DESC', 'ASC'] and
                 by  in ['updated', 'created'] ):
            return self.write(u'wrong URL !')

        SQL = "\
SELECT id, name, summary, user_id, catalog_id, logoname, \
       filesize, is_useable, popularity, created, updated \
FROM appliance \
WHERE catalog_id=%s \
ORDER BY %s %s \
LIMIT %s OFFSET %s;" % ( catalog_id, by, sort, page_size, (cur_page - 1) * page_size )

        apps = self.db.query(SQL)

        catalogs = self.db.query( '\
SELECT id, name, position FROM appliance_catalog \
ORDER BY position;' )

        total = len( self.db.query('\
SELECT id FROM appliance WHERE catalog_id=%s;', catalog_id) )
        pagination = Pagination( total = total,
                                 page_size = page_size,
                                 cur_page = cur_page )

        page_html = pagination.html(self.get_page_url)

        d = { 'title': "Appliance Home",
              'appliances': apps,
              'catalogs': catalogs,
              'cur_catalog': catalog_id,
              'page_html': page_html }

        self.render("appliance/index.html", **d)



class Upload(AppRequestHandler):

    @authenticated
    def get(self):

        d = { 'title': "Upload Appliance" }
        self.render("appliance/upload_appliance.html", **d)

    @authenticated
    def post(self):

        # pull in details created by the nginx upload module
        fname = self.get_argument('upfile_name', None)
        fsize = self.get_argument('upfile_size', -1)
        fhash = self.get_argument('upfile_md5', '')
        fpath = self.get_argument('upfile_path', None)

        d = { 'fname': fname, 'fsize': fsize,
              'fhash': fhash, 'fpath': fpath }

        # make sure the arguments is correct !
        if not ( fname and fpath and fsize > 0 and fhash):
            raise HTTPError(400, "arguments error !")

        # TODO: make sure upfile is correct !

        # copy the upfile from fpath to LuoYun System
        msg = self.save_upfile(fpath, fhash)
        if msg:
            d['error'] = msg
            self.set_status(400)
            return self.done(
                _('Save %s failed: %s') % (fname, msg) )

        # add appliance to DB
        try:
            self.db.execute(
                "INSERT INTO appliance (name, user_id, \
filesize, checksum, created, updated) VALUES \
(%s, %s, %s, %s, 'now', 'now');",
                fname.replace('.', '_').upper(),
                self.current_user.id, fsize, fhash )

            appliance = self.db.get(
                'SELECT id from appliance WHERE checksum=%s;',
                fhash )

            # go to edit for appliance
            self.redirect('/appliance/%s/edit' % appliance.id)

        except Exception, emsg:
            return self.done( 'DB: %s' % emsg )


    def save_upfile(self, fpath, fhash):

        if not os.path.exists(fpath):
            return "Can not found %s" % fpath

        appdir = self.application.settings["appliance_top_dir"]

        if not os.path.exists(appdir):
            try:
                os.mkdir(appdir)
            except OSError, emsg:
                return "mkdir error: %s" % emsg

        # file exists ?
        dpath = "%sappliance_%s" % (appdir, fhash)
        if os.path.exists(dpath):
            return "%s exists !" % dpath

        if ( os.stat(fpath).st_dev !=
             os.stat(appdir).st_dev ):
            # not in same partition, use copy
            return "copy have not complete !"

        else:
            # in same partition, use hard link
            try:
                os.link(fpath, dpath)
                os.unlink(fpath)
                return None # no news is good news !
            except OSError, emsg:
                return "OSError: %s" % emsg
            except:
                return "link, unlink error !"
        


class Edit(LyRequestHandler):


    def initialize(self):
        self.d = { 'title': "Edit Appliance", 'ERROR': [] }

        self.d['catalogs'] = self.db.query(
            "SELECT id, name FROM appliance_catalog;")

        self.t = 'appliance/edit.html'

    @authenticated
    def prepare(self):

        id = re.match('.*/([0-9]+)/.*', self.request.path).groups()[0]

        app = self.db.get('SELECT * from appliance WHERE id=%s;', id)
        if not app:
            self.write(u'Have not found appliance %s !' % id)
            return self.finish()

        if self.current_user.id not in [app.user_id, 1]:
            self.write(u"Can not edit appliance !")
            return self.finish()

        self.d['id'] = id
        self.d['catalog'] = self.db.get( 'SELECT id, name \
FROM appliance_catalog WHERE id=%s;', app.catalog_id )

        self.d['appliance'] = app
        self.d['name'] = self.get_argument('name', app.name)

        self.d['catalog_id'] = int( self.get_argument(
                'catalog',
                app.catalog_id if app.catalog_id else 0) )


    def get(self, id):

        self.render(self.t, **self.d)


    def post(self, id):

        d = self.d

        if not self.parameter_ok():
            return self.render(self.t, **d)

        # Save logo file
        if self.request.files:
            logoname = self.save_logo()
            if d['ERROR']:
                return self.render(self.t, **d)

        # Updated DB
        try:
            self.db.execute(
                'UPDATE appliance SET name=%s, \
catalog_id=%s, updated=%s, logoname=%s WHERE id=%s;',
                d['name'], d['catalog_id'], 'now',
                logoname, id )

            self.redirect('/appliance/%s' % id)

        except Exception, emsg:
            d['ERROR'].append(emsg)
            self.render(self.t, **d)


    def save_logo(self):

        d = self.d
        logoname = self.d['appliance'].logoname

        support_image = ['jpg', 'png', 'jpeg', 'gif', 'bmp']
        for f in self.request.files['logo']:

            if len(f['body']) > 2097152: # 2M
                d['ERROR'].append(
                    u'Logo file must smaller than 2M !')
                break

            ftype = 'unknown'
            x = f['content_type'].split('/')
            if len(x) == 2:
                ftype = x[-1]
            else:
                x = f['filename'].split('.')
                if len(x) == 2:
                    ftype = x[-1]

            ftype = ftype.lower()

            if ftype not in support_image:
                d['ERROR'].append(
                    u'No support image, support is %s' %
                    support_image )
                break

            p = self.settings['appliance_top_dir']
            fname = 'logo_%s.%s' % (d['id'], ftype)
            fpath = '%s/%s' % (p, fname)

            try:
                savef = file(fpath, 'w')
                savef.write(f['body'])
                savef.close()
                logoname = fname
                break # Just one upload file

            except Exception, emsg:
                d['ERROR'].append(emsg)
                break

        return logoname


    def parameter_ok(self):

        d = self.d

        catalogs = [ x.id for x in d['catalogs'] ]
        if d['catalog_id'] not in catalogs:
            d['ERROR'].append(u'wrong catalog !')

        if len(d['name']) == 0:
            self.d['ERROR'].append(u'have not give name !')
        elif len(d['name']) < 3:
            self.d['ERROR'].append(u'name is too short !')

        return d['ERROR'] == []


class Delete(AppRequestHandler):


    @authenticated
    def get(self, id):

        d = { 'title': "Delete Appliance", 'id': id }

        app = self.db.get(
            'SELECT * from appliance WHERE id=%s;', id )

        if not app:
            msg = _('Have not found appliance %s !') % id
            return self.done(msg)

        # auth delete
        if self.current_user.id not in [app.user_id, 1] :
            msg = _('No permissions to delete appliance !')
            return self.done(msg)


        # Delete appliance file
        dpath = "%sappliance_%s" % (
            self.settings["appliance_top_dir"], app.checksum )

        if os.path.exists(dpath):
            try:
                os.unlink(dpath)
            except Exception, emsg:
                msg = _('Delete %s failed: %s') % (
                    dpath, emsg )
                return self.done(msg)
        else:
            logging.warning("%s did not exist !" % dpath)

        # DELETE appliance row from DB
        try:
            self.db.execute(
                'DELETE FROM appliance WHERE id = %s;', id)

        except Exception, emsg:
            raise HTTPError( 500, 'DB: %s' % emsg)

        msg = 'Delete appliance %s success !' % id
        return self.done(msg)



class View(AppRequestHandler):

    def get(self, id):

        ajax = self.get_argument('ajax', 0)

        app = self.db.get('SELECT * from appliance WHERE id=%s;', id )

        if not app:
            return self.render(
                'appliance/action_result.html',
                msg = 'Have not found appliance %s !' % id)

        instances = self.db.query(
            'SELECT * FROM instance WHERE appliance_id=%s',
            app.id )

        d = { 'title': "View Appliance", 'appliance': app,
              'instances': instances }

        if ajax:
            self.render('appliance/view_by_ajax.html', **d)
        else:
            self.render('appliance/view.html', **d)



class CreateInstance(LyRequestHandler):

    @authenticated
    def get(self, id):

        app = self.db.get(
            'SELECT * from appliance WHERE id=%s;', id )

        if not app:
            return self.render(
                'appliance/action_result.html',
                msg = 'Have not found appliance %s !' % id)

        d = { 'title': 'Create Instance', 'appliance': app,
              'name': '%s_%s' % (
                self.current_user.username, app.name) }

        self.render('appliance/create_instance.html', **d)


