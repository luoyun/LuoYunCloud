# coding: utf-8

import os, logging, re, tempfile, Image
import settings

from lycustom import LyRequestHandler
from tornado.web import authenticated, HTTPError

from sqlalchemy.sql.expression import asc, desc

from app.instance.models import Instance
from app.appliance.models import Appliance, ApplianceCatalog
from app.appliance.forms import EditApplianceForm

from lycustom import has_permission
from lytool.filesize import size as human_size
from ytool.pagination import pagination



class AppRequestHandler(LyRequestHandler):


    def done(self, msg):

        ajax = self.get_argument_int('ajax', 0)

        if ajax:
            self.write(msg)
        else:
            self.render( 'appliance/action_result.html',
                         msg = msg )


    def get_appliance(self, id, isowner=False):

        app = self.db2.query(Appliance).get(id)

        if not app:
            self.done( _('No such appliance: %s !') % id )
            return None

        if app.isprivate:
            if ( (not self.current_user) or (
                    (self.current_user.id != app.user_id) and
                    (not self.has_permission('admin')) )
                 ):
                self.done( _('Appliance %s is private !') % id )
                return None

        # Just user can do
        if isowner:
            if app.user_id != self.current_user.id:
                self.done( _('Only owner can do this!') )
                return None

        return app




class Index(AppRequestHandler):

    def initialize(self, title = _('Appliance Home')):
        self.title = title

    def get(self):

        catalog_id = self.get_argument_int('c', 1)
        page_size = self.get_argument_int('sepa', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'updated')
        sort = self.get_argument('sort', 'DESC')

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        apps = self.db2.query(Appliance).filter_by(
            catalog_id=catalog_id).filter_by(
            isprivate=False).order_by(by_exp)

        total = apps.count()
        apps = apps.slice(start, stop)
            
        catalogs = self.db2.query(ApplianceCatalog).all()
        for c in catalogs:
            c.total = self.db2.query(Appliance.id).filter_by(
                catalog_id = c.id ).filter_by(
                isprivate=False).count()

        page_html = pagination(self.request.uri, total,  page_size, cur_page)

        d = { 'title': self.title,
              'appliances': apps,
              'catalogs': catalogs,
              'cur_catalog': catalog_id,
              'page_html': page_html }

        self.render("appliance/index.html", **d)



class Upload(AppRequestHandler):

    @has_permission('appliance.upload')
    def get(self):

        d = { 'title': _("Upload Appliance") }
        self.render("appliance/upload_appliance.html", **d)


    @has_permission('appliance.upload')
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
            self.choices.append( (str(s.id), s.name) )


    def get_app(self, ID):

        appliance = self.db2.query(Appliance).get(ID)

        if appliance.user_id != self.current_user.id:
            return None

        return appliance

 
    def get(self, ID):

        appliance = self.get_app(ID)
        if not appliance:
            return self.write( _('No permission!') )

        form = EditApplianceForm()
        form.catalog.choices = self.choices
        form.catalog.default = appliance.catalog_id

        form.os.default = appliance.os

        form.process()

        form.name.data = appliance.name
        form.summary.data = appliance.summary
        form.description.data = appliance.description

        return self.render( 'appliance/edit.html', title = _('Edit Appliance '), form = form, appliance = appliance )


    def post(self, ID):

        appliance = self.get_app(ID)
        if not appliance:
            return self.write( _('No permission!') )

        form = EditApplianceForm( self.request.arguments )
        form.catalog.choices = self.choices

        if form.validate():
            appliance.name = form.name.data
            appliance.os = self.get_int(form.os.data)
            appliance.summary = form.summary.data
            appliance.catalog_id = form.catalog.data
            appliance.description = form.description.data

            # Save logo file
            if self.request.files:
                r = self.save_logo(appliance)
                if r:
                    form.logo.errors.append( r )

            try:
                self.db2.commit()
                if not form.logo.errors:
                    url = self.reverse_url( 'appliance:view', appliance.id )
                    return self.redirect( url )

            except Exception, emsg:
                form.description.errors.append( _('Save appliance info to DB failed: %s' % emsg ) )

        d = { 'title': _('Edit Appliance "%s"') % appliance.name,
              'form': form, 'appliance': appliance }
        self.render( 'appliance/edit.html', **d )


    def save_logo(self, appliance):

        if not os.path.exists(appliance.logodir):
            try:
                os.makedirs(appliance.logodir)
            except Exception, e:
                return _('create appliance logo dir "%s" failed: %s') % (appliance.logodir, e)

        max_size = settings.APPLIANCE_LOGO_MAXSIZE
        logoname = settings.APPLIANCE_LOGO_NAME

        for f in self.request.files['logo']:

            if len(f['body']) > max_size:
                return _('Picture must smaller than %s !') % human_size(max_size)

            tf = tempfile.NamedTemporaryFile()
            tf.write(f['body'])
            tf.seek(0)

            try:
                img = Image.open(tf.name)
            except Exception, emsg:
                return _('Open %s failed: %s , is it a picture ?') % (f.get('filename'), emsg)

            try:
                # can convert image type
                img.save(appliance.logopath)
 
                img.thumbnail(settings.APPLIANCE_LOGO_THUM_SIZE, resample=1)
                img.save(appliance.logothum)
 
                tf.close()

            except Exception, emsg:
                return _('Save %s failed: %s') % (f.get('filename'), emsg)



class Delete(AppRequestHandler):

    @authenticated
    def get(self, ID):

        A = self.db2.query(Appliance).get(ID)
        d = {'A': A, 'E': []}

        if not A:
            d['E'].append( _('Can not find appliance %s.') % ID )
            return self.end(d)

        # auth delete
        if  not (self.current_user.id == A.user_id or self.has_permission('admin')):
            d['E'].append( _('No permission !') )
            return self.end(d)

        # TODO: have any instances exist ?
        IL = self.db2.query(Instance).filter_by(appliance_id=ID).all()
        if IL:
            d['E'].append( _('Have instances exist') )
            return self.end(d)

        # Delete appliance file
        dpath = "%sappliance_%s" % (
            self.settings["appliance_top_dir"], A.checksum )

        if os.path.exists(dpath):
            try:
                os.unlink(dpath)
            except Exception, emsg:
                d['E'].append( _('Delete %s failed: %s') % ( dpath, emsg ) )
                return self.end(d)
        else:
            logging.warning("%s did not exist !" % dpath)

        # DELETE appliance row from DB
        self.db2.delete(A)
        self.db2.commit()

        d['E'].append( 'Delete appliance %s success !' % ID )
        self.render('appliance/delete_return.html', **d)


    def end(self, d):
        self.render('appliance/delete_return.html', **d)



class View(AppRequestHandler):


    def get(self, id):

        app = self.get_appliance(id)
        if not app:
            return self.render(
                'appliance/action_result.html',
                msg = 'Have not found appliance %s !' % id )

        instances, page_html = self.page_view_instances(app)

        d = { 'title': _("View Appliance"), 'appliance': app,
              'instances': instances, 'page_html': page_html }

        self.render('appliance/view.html', **d)


    def page_view_instances(self, app):

        view = self.get_argument('view', 'all')
        by = self.get_argument('by', 'updated')
        sort = self.get_argument('sort', 'desc')
        status = self.get_argument('status', 'all')
        page_size = self.get_argument_int(
                'sepa', settings.APPLIANCE_INSTANCE_LIST_PAGE_SIZE)

        cur_page = self.get_argument_int('p', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        if status == 'running':
            slist = settings.INSTANCE_SLIST_RUNING
        elif status == 'stoped':
            slist = settings.INSTANCE_SLIST_STOPED
        else:
            slist = settings.INSTANCE_SLIST_ALL

        instances = self.db2.query(Instance).filter(
            Instance.isprivate != True ).filter(
            Instance.status.in_( slist) ).filter(
            Instance.appliance_id == app.id)
            

        if view == 'self' and self.current_user:
            instances = instances.filter_by(
                user_id = self.current_user.id )

        if by == 'created':
            by_obj = Instance.created
        else:
            by_obj = Instance.updated

        sort_by_obj = desc(by_obj) if sort == 'desc' else asc(by_obj)

        instances = instances.order_by( sort_by_obj )

        total = instances.count()
        instances = instances.slice(start, stop).all()

        page_html = pagination(self.request.uri, total,  page_size, cur_page)

        return instances, page_html
        


class SetUseable(AppRequestHandler):

    @authenticated
    def get(self, id):

        # TODO:
        url = self.get_argument('next_url', None)
        if not url:
            url = self.reverse_url('appliance:view', id)

        app = self.db2.query(Appliance).get(id)
        if not app:
            return self.write( _('No such appliance!') )

        if not ( app.user_id == self.current_user.id or
                 self.has_permission('admin') ):
            return self.write( _('No permission!') )

        flag = self.get_argument('flag', None)
        app.isuseable = True if flag == 'true' else False
        self.db2.commit()

        self.redirect( url )



class SetPrivate(AppRequestHandler):

    @authenticated
    def get(self, id):

        # TODO:
        url = self.get_argument('next_url', None)
        if not url:
            url = self.reverse_url('appliance:view', id)

        app = self.db2.query(Appliance).get(id)
        if not app:
            return self.write( _('No such appliance !') )

        if not ( app.user_id == self.current_user.id or
                 self.has_permission('admin') ):
            return self.write( _('No permission!') )

        flag = self.get_argument('flag', None)
        app.isprivate = True if flag == 'true' else False
        self.db2.commit()

        self.redirect( url )


class islockedToggle(LyRequestHandler):
    ''' Toggle islocked flag '''

    @has_permission('admin')
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        A = self.db2.query(Appliance).get(ID)

        if A:
            A.islocked = not A.islocked
            self.db2.commit()
            # no news is good news

        else:
            self.write( _('Can not find appliance %s.') % ID )


class isuseableToggle(LyRequestHandler):
    ''' Toggle isuseable flag '''

    @authenticated
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        A = self.db2.query(Appliance).get(ID)

        if A:
            if not ( self.current_user.id == A.user_id or
                     has_permission('admin') ):
                return self.write( _('No permissions !') )

            A.isuseable = not A.isuseable
            self.db2.commit()
            # no news is good news

        else:
            self.write( _('Can not find appliance %s.') % ID )


class tuneCatalogPosition(LyRequestHandler):
    ''' change catalog position '''

    @has_permission('admin')
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        C = self.db2.query(ApplianceCatalog).get(ID)

        if C:
            n = self.get_argument_int('value', 0)
            if n:
                C.position += n
                self.db2.commit()
                # no news is good news
            else:
                self.write( _('tune value must be a integer.') )

        else:
            self.write( _('Can not find appliance catalog %s') % ID )

