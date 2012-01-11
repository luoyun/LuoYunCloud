# coding: utf-8

import os, logging
import settings

from lycustom import LyRequestHandler
from tornado.web import authenticated, HTTPError


class Index(LyRequestHandler):

    def get(self):

        apps = self.db.query("SELECT * FROM appliance;")
        catalogs = self.db.query("SELECT * FROM appliance_catalog;")

        for c in catalogs:
            c.apps = self.db.query(
                'SELECT * FROM appliance WHERE catalog_id=%s;',
                c.id )

        d = { 'title': "Appliance Home",
              'appliances': apps,
              'catalogs': catalogs }

        self.render("appliance/index.html", **d)


class Upload(LyRequestHandler):

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
            return self.render("appliance/upload_failed.html", **d)

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

        except:
            #self.set_status(400)
            d['error'] = 'Add appliance to DB error !'
            self.render("appliance/upload_failed.html", **d)


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

    def failed(self, msg):
        self.render('appliance/action_failed.html',reason = msg)

    @authenticated
    def get(self, id):

        try:
            app = self.db.get(
                'SELECT * from appliance WHERE id=%s;', id )
        except:
            return self.failed("Have not found %s !" % id)

        if not app:
            return self.failed('Have not found appliance %s !' % id)

        # auth delete
        if app.user_id != self.current_user.id:
            # TODO: admin can do anything
            return self.failed("Just owner can edit this appliance !")

        catalogs = self.db.query("SELECT * FROM appliance_catalog;")

        d = { 'title': "Edit Appliance",
              'appliance': app,
              'catalogs': catalogs }

        self.render("appliance/edit.html", **d)



    @authenticated
    def post(self, id):

        try:
            app = self.db.get(
                'SELECT * from appliance WHERE id=%s;', id )

        except:
            return self.write("Have not found %s !" % id)

        name = self.get_argument("name")
        catalog_id = int(self.get_argument("catalog"))

        try:
            self.db.execute(
                'UPDATE appliance SET name=%s, catalog_id=%s, updated=%s where id=%s;',
                name, catalog_id, 'now', id )
            self.redirect('/appliance/%s' % id)
        except:
            d = {'appliance': app,
                 'submit_error': 'UPDATA DB error !' }
            self.render("appliance/edit.html", **d)


class Delete(LyRequestHandler):

    def failed(self, dic, reason = None):
        dic['reason'] = reason
        self.render('appliance/action_failed.html', **dic)

    @authenticated
    def get(self, id):

        d = { 'title': "Delete Appliance", 'id': id }

        try:
            app = self.db.get(
                'SELECT * from appliance WHERE id=%s;', id )
        except:
            return self.failed(d,"Query DB error !") 

        if not app:
            return self.failed(d, 'Have not found %s !' % id)

        # auth delete
        if app.user_id != self.current_user.id:
            # TODO: admin can do anything
            return self.failed(d, "Just owner can delete this appliance !")

        # Delete appliance file
        dpath = "%sappliance_%s" % (
            self.application.settings["appliance_top_dir"],
            app.checksum )
        if os.path.exists(dpath):
            try:
                os.unlink(dpath)
            except:
                return self.failed(d, "Delete %s failed !" % dpath)
        else:
            logging.warning("%s did not exist !" % dpath)

        # DELETE appliance row from DB
        try:
            self.db.execute('DELETE FROM appliance WHERE id = %s;', id)
        except:
            raise HTTPError(500, 'DELETE appliance %s from DB failed !' % id)

        self.render('appliance/action_success.html',
                    msg = 'Delete appliance %s success !' % id)



class View(LyRequestHandler):

    def get(self, id):

        app = self.db.get('SELECT * from appliance WHERE id=%s;', id )

        if not app:
            return self.render('appliance/action_failed.html',
                               reason = 'Have not found appliance %s !' % id)

        d = { 'title': "View Appliance", 'appliance': app }

        self.render("appliance/view.html", **d)



class CreateInstance(LyRequestHandler):

    @authenticated
    def get(self, id):

        app = self.db.get('SELECT * from appliance WHERE id=%s;', id )

        if not app:
            return self.render('appliance/action_failed.html',
                               reason = 'Have not found appliance %s !' % id)

        d = { 'title': 'Create Instance', 'appliance': app,
              'name': '%s_%s' % (self.current_user.username, app.name) }

        self.render('appliance/create_instance.html', **d)


class AddCatalog(LyRequestHandler):

    @authenticated
    def get(self):

        # TODO: just admin could add catalog

        self.render('appliance/add_catalog.html',
                    title = 'Add Appliance Catalog')


    @authenticated
    def post(self):

        d = { 'title': 'Add appliance catalog' }

        d['name'] = self.get_argument('name', '')
        d['summary'] = self.get_argument('summary', '')
        d['description'] = self.get_argument('description', '')

        if not d['name']:
            d['name_error'] = 'Name is required !'
            return self.render('appliance/add_catalog.html', **d)

        try:
            self.db.execute(
                "INSERT INTO appliance_catalog (name, summary, description, created, updated) VALUES (%s, %s, %s, 'now', 'now');",
                d['name'], d['summary'], d['description'] )
        except Exception, emsg:
            return self.write('Add catalog to DB failed: %s' % emsg)

        self.redirect('/appliance')
        
