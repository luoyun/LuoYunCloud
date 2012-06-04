# coding: utf-8

import os, logging, re
import settings

from lycustom import LyRequestHandler, Pagination
from tornado.web import authenticated, HTTPError

from sqlalchemy.sql.expression import asc, desc

from app.instance.models import Instance
from app.appliance.models import Appliance, ApplianceCatalog
from app.appliance.forms import EditApplianceForm



class AppRequestHandler(LyRequestHandler):


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

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        apps = self.db2.query(Appliance).filter_by(
            catalog_id=catalog_id).order_by(by_exp).slice(start, stop)
            
        catalogs = self.db2.query(ApplianceCatalog).all()
        for c in catalogs:
            c.total = self.db2.query(Appliance.id).filter_by( catalog_id = c.id ).count()

        pagination = Pagination(
            total = self.db2.query(Appliance.id).count(),
            page_size = page_size, cur_page = cur_page )

        page_html = pagination.html( self.get_page_url )

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

        newapp = Appliance( name=fname.replace('.', ' '),
                            user=self.current_user,
                            filesize=fsize,
                            checksum=fhash )
        self.db2.add(newapp)
        self.db2.commit()

        url = self.reverse_url( 'appliance:edit', newapp.id )
        self.redirect(url)



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
            # TODO: redirect to edit !
            #self.redirect('/appliance/%s/edit' % appliance.id)

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

    @authenticated
    def prepare(self):

        self.choices = []
        for s in self.db2.query(ApplianceCatalog.id, ApplianceCatalog.name).all():
            self.choices.append( (s.id, s.name) )

 
    def get(self, id):

        appliance = self.db2.query(Appliance).get(id)

        if appliance.user_id != self.current_user.id:
            return self.write( _('You have not permissions !') )

        form = EditApplianceForm()
        form.name.data = appliance.name
        form.summary.data = appliance.summary
        form.description.data = appliance.description

        form.catalog.choices = self.choices
        form.catalog.default = appliance.catalog_id

        return self.render( 'appliance/edit.html', title = _('Edit Appliance '), form = form, appliance = appliance )


    def post(self, id):

        appliance = self.db2.query(Appliance).get(id)

        if appliance.user_id != self.current_user.id:
            return self.write( _('You have not permissions !') )

        form = EditApplianceForm( self.request.arguments )

        appliance.name = form.name.data
        appliance.summary = form.summary.data
        appliance.catalog_id = form.catalog.data
        appliance.description = form.description.data

        # Save logo file
        if self.request.files:
            r = self.save_logo(appliance)
            if r: return self.write( _('%s') % r )

        try:
            self.db2.commit()
            url = self.reverse_url( 'appliance:view', appliance.id )
            return self.redirect( url )

        except Exception, emsg:
            form.description.errors.append( _('DB : %s' % emsg ) )
        self.render( 'appliance/edit.html', title = _('Edit Appliance'), form = form, appliance = appliance )


    def save_logo(self, appliance):

        support_image = ['jpg', 'png', 'jpeg', 'gif', 'bmp']
        for f in self.request.files['logo']:

            if len(f['body']) > 2097152: # 2M
                return _('Logo file must smaller than 2M !')

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
                return _('No support image, support is %s' % support_image )

            p = self.settings['appliance_top_dir']
            fname = 'logo_%s.%s' % (appliance.id, ftype)
            fpath = '%s/%s' % (p, fname)
            try:
                savef = file(fpath, 'w')
                savef.write(f['body'])
                savef.close()
                appliance.logoname = fname
                break # Just one upload file

            except Exception, emsg:
                return emsg



class Delete(AppRequestHandler):


    @authenticated
    def get(self, id):

        app = self.db2.query(Appliance).get(id)
        if not app:
            msg = _('Have not found appliance %s !') % id
            return self.done( msg )

        # auth delete
        if self.current_user.id != app.user_id:
            msg = _('No permissions to delete appliance !')
            return self.done( msg )

        # TODO: have any instances exist ?
        inst_list = self.db2.query(Instance).filter_by( appliance_id=app.id ).all()
        if inst_list:
            return self.render('appliance/delete_failed.html',
                               ERROR = _('Have instances exist'),
                               INSTANCE_LIST = inst_list )


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
        self.db2.delete(app)
        self.db2.commit()

        msg = 'Delete appliance %s success !' % id
        return self.done(msg)



class View(AppRequestHandler):


    def get(self, id):

        ajax = self.get_argument('ajax', 0)

        app = self.db2.query(Appliance).get(id)
        if not app:
            return self.render(
                'appliance/action_result.html',
                msg = 'Have not found appliance %s !' % id )

        instances = self.db2.query(Instance).filter_by( appliance_id=app.id ).all()

        d = { 'title': "View Appliance", 'appliance': app,
              'instances': instances }

        if ajax:
            self.render('appliance/view_by_ajax.html', **d)
        else:
            self.render('appliance/view.html', **d)



class CreateInstance(LyRequestHandler):

    @authenticated
    def get(self, id):

        app = self.db2.query(Appliance).get(id)
        if not app:
            return self.render(
                'appliance/action_result.html',
                msg = 'Have not found appliance %s !' % id)

        d = { 'title': 'Create Instance', 'appliance': app,
              'name': "%s's %s" % (
                self.current_user.username, app.name) }

        self.render('appliance/create_instance.html', **d)

