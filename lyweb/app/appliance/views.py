# coding: utf-8

import os, logging, re, tempfile, Image
import settings

from lycustom import RequestHandler
from tornado.web import authenticated, HTTPError

from sqlalchemy.sql.expression import asc, desc

from app.instance.models import Instance
from app.appliance.models import Appliance, ApplianceCatalog, \
    ApplianceScreenshot

from lycustom import has_permission
from yweb.utils.filesize import size as human_size
from yweb.utils.pagination import pagination


class AppRequestHandler(RequestHandler):


    def render404(self, msg):

        self.set_status(404)
        self.render('appliance/404.html', msg = msg)


    def done(self, msg):

        ajax = self.get_argument_int('ajax', 0)

        if ajax:
            self.write(msg)
        else:
            self.render( 'appliance/action_result.html',
                         msg = msg )


    def get_appliance_byid(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return None, _('Give appliance id please.')

        A = self.db.query(Appliance).get(ID)
        if not A:
            return None, _('Can not find appliance %s') % ID

        if A.isprivate:
            if ( (not self.current_user) or (
                    (self.current_user.id != A.user_id) and
                    (not self.has_permission('admin')) ) ):
                return None, _('Appliance %s is private !') % ID

        return A, None



class Index(AppRequestHandler):

    def initialize(self, title = None):
        self.title = self.trans(_('Appliance Home'))

    def get(self):

        catalog_id = self.get_argument_int('c', 0)
        page_size = self.get_argument_int('sepa', 24)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'updated')
        sort = self.get_argument('sort', 'DESC')

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        apps = self.db.query(Appliance).filter_by(isprivate=False)

        if catalog_id:
            apps = apps.filter_by(catalog_id=catalog_id)

        total = apps.count()

        apps = apps.order_by(by_exp)
        apps = apps.slice(start, stop)
            
        catalogs = self.db.query(ApplianceCatalog).all()
        for c in catalogs:
            c.total = self.db.query(Appliance.id).filter_by(
                catalog_id = c.id ).filter_by(
                isprivate=False).count()

        page_html = pagination(self.request.uri, total,  page_size, cur_page)

        d = { 'title': self.title,
              'appliances': apps,
              'appliance_total': total,
              'catalogs': catalogs,
              'cur_catalog': catalog_id,
              'page_html': page_html }

        self.render("appliance/index.html", **d)



class Upload(AppRequestHandler):

    @has_permission('appliance.upload')
    def get(self):

        d = { 'title': self.trans(_("Upload Appliance")) }
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

        # Make sure appliance exists:
        A = self.db.query(Appliance).filter_by(
            checksum = fhash ).first()

        if A:
            if not ( A.user_id == self.current_user.id or
                     self.has_permission('admin') ):
                return self.done( _('Appliance exists, but you have not any permission to management it.') )

        else:
            
            # copy the upfile from fpath to LuoYun System
            msg = self.save_upfile(fpath, fhash)
            if msg:
                d['error'] = msg
                self.set_status(400)
                return self.done(
                    self.trans(_('Save %(filename)s failed: %(emsg)s')) % {
                        'filename': fname, 'emsg': msg } )

            A = Appliance( name=fname.replace('.', ' '),
                           user=self.current_user,
                           filesize=fsize,
                           checksum=fhash )
            self.db.add( A )
            self.db.commit()

        url = self.reverse_url( 'myun:appliance:baseinfo:edit')
        url += '?id=%s' % A.id
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
            #return "%s exists !" % dpath
            # TODO: exists is ok! but should match db record.
            return None
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
        


class Delete(AppRequestHandler):

    @authenticated
    def get(self, ID):

        A = self.db.query(Appliance).get(ID)
        d = {'A': A, 'E': []}

        if not A:
            d['E'].append( self.trans(_('Can not find appliance %s.')) % ID )
            return self.end(d)

        # auth delete
        if  not (self.current_user.id == A.user_id or self.has_permission('admin')):
            d['E'].append( self.trans(_('No permission !')) )
            return self.end(d)

        # TODO: have any instances exist ?
        IL = self.db.query(Instance).filter_by(appliance_id=ID).all()
        if IL:
            d['E'].append( self.trans(_('Have instances exist')) )
            return self.end(d)

        # Delete appliance file
        dpath = "%sappliance_%s" % (
            self.settings["appliance_top_dir"], A.checksum )

        if os.path.exists(dpath):
            try:
                os.unlink(dpath)
            except Exception, emsg:
                d['E'].append( self.trans(_('Delete %(filename)s failed: %(emsg)s')) % {
                        'filename': dpath, 'emsg': emsg } )
                return self.end(d)
        else:
            logging.warning("%s did not exist !" % dpath)

        # DELETE appliance row from DB
        self.db.delete(A)
        self.db.commit()

        d['E'].append( 'Delete appliance %s success !' % ID )
        self.render('appliance/delete_return.html', **d)


    def end(self, d):
        self.render('appliance/delete_return.html', **d)



class View(AppRequestHandler):


    def get(self):

        A, msg = self.get_appliance_byid()
        if not A:
            return self.render404( msg )

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

        instances = self.db.query(Instance).filter(
            Instance.isprivate != True ).filter(
            Instance.status.in_( slist) ).filter(
            Instance.appliance_id == A.id)
            

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

        d = { 'title': _('View Appliance "%s"') % A.name,
              'appliance': A,
              'instances': instances,
              'page_html': page_html }

        self.render('appliance/view.html', **d)


        
class SetUseable(AppRequestHandler):

    @authenticated
    def get(self, id):

        # TODO:
        url = self.get_argument('next_url', None)
        if not url:
            url = self.reverse_url('appliance:view', id)

        app = self.db.query(Appliance).get(id)
        if not app:
            return self.write( self.trans(_('No such appliance!')) )

        if not ( app.user_id == self.current_user.id or
                 self.has_permission('admin') ):
            return self.write( self.trans(_('No permission!')) )

        flag = self.get_argument('flag', None)
        app.isuseable = True if flag == 'true' else False
        self.db.commit()

        self.redirect( url )



class SetPrivate(AppRequestHandler):

    @authenticated
    def get(self, id):

        # TODO:
        url = self.get_argument('next_url', None)
        if not url:
            url = self.reverse_url('appliance:view', id)

        app = self.db.query(Appliance).get(id)
        if not app:
            return self.write( self.trans(_('No such appliance !')) )

        if not ( app.user_id == self.current_user.id or
                 self.has_permission('admin') ):
            return self.write( self.trans(_('No permission!')) )

        flag = self.get_argument('flag', None)
        app.isprivate = True if flag == 'true' else False
        self.db.commit()

        self.redirect( url )


class islockedToggle(RequestHandler):
    ''' Toggle islocked flag '''

    @has_permission('admin')
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        A = self.db.query(Appliance).get(ID)

        if A:
            A.islocked = not A.islocked
            self.db.commit()
            # no news is good news

        else:
            self.write( self.trans(_('Can not find appliance %s.')) % ID )


class isuseableToggle(RequestHandler):
    ''' Toggle isuseable flag '''

    @authenticated
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        A = self.db.query(Appliance).get(ID)

        if A:
            if not ( self.current_user.id == A.user_id or
                     has_permission('admin') ):
                return self.write( self.trans(_('No permissions !')) )

            A.isuseable = not A.isuseable
            self.db.commit()
            # no news is good news

        else:
            self.write( self.trans(_('Can not find appliance %s.')) % ID )


class tuneCatalogPosition(RequestHandler):
    ''' change catalog position '''

    @has_permission('admin')
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        C = self.db.query(ApplianceCatalog).get(ID)

        if C:
            n = self.get_argument_int('value', 0)
            if n:
                C.position += n
                self.db.commit()
                # no news is good news
            else:
                self.write( self.trans(_('tune value must be a integer.')) )

        else:
            self.write( self.trans(_('Can not find appliance catalog %s')) % ID )



class AttrSet(RequestHandler):
    ''' set appliance attr '''

    def myfinish(self, string, code=1, data=[]):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        d = { 'string': string, 'code': code, 'data': data }

        self.write( d )
        self.finish()


    @authenticated
    def post(self):

        ID = self.get_argument('id', '')
        if not ID:
            return self.myfinish(
                _('Please give me the appliance id.') )

        ID_LIST = [ self.get_int(x) for x in ID.split(',') ]

        attr = self.get_argument('attr', None)
        value = self.get_argument('value', '').lower().strip()

        if not attr:
            return self.myfinish( _('No attr find.') )

        if attr not in ['isprivate', 'isuseable']:
            return self.myfinish( _('Can not support attr: %s') % attr )

        if not value:
            return self.myfinish( _('No value find.') )

        self.attr = attr
        self.value = value

        isadmin = has_permission('admin')
        myid = self.current_user.id

        data = []
        for ID in ID_LIST:
            
            d = { 'code': 1, 'id': ID }

            A = self.db.query(Appliance).get(ID)

            if A:

                if ( myid == A.user_id or isadmin ):
                    _call = getattr(self, 'set_' + attr)
                    r = _call( A )
                    if r:
                        d['string'] = r
                    else:
                        d['code'] = 0
                else:
                    d['string'] = _('No permissions to set attr')
            else:
                d['string'] = _('Can not find instance %s.') % ID

            data.append( d )

        self.db.commit()

        code = 0
        string = _('Set attr (%s) success.') % attr
        for x in data:
            if d['code']:
                string = _('Have something failed.')
                code = 1

        self.myfinish(string = string, code = code, data = data)


    def set_isprivate(self, A):

        if self.value == 'true':
            A.isprivate = True
        elif self.value == 'false':
            A.isprivate = False
        else:
            return self.trans(
                _('Invalid value for attr "isprivate" : %s') % value )


    def set_isuseable(self, A):

        if self.value == 'true':
            A.isuseable = True
        elif self.value == 'false':
            A.isuseable = False
        else:
            return self.trans(
                _('Invalid value for attr "isuseable" : %s') % value )



class ScreenshotHandler(RequestHandler):

    def get_appliance(self):

        ID = self.get_argument_int('appliance_id', None)
        if not ID:
            return None, _('Give me appliance_id please.')

        A = self.db.query(Appliance).get( ID )
        if not A:
            return None, _('Can not find appliance %s') % ID

        if not ( A.user_id == self.current_user.id or
                 self.has_permission('admin') ):
            return None, _('No permission to manage screenshot')

        return A, None

    def get_screenshot(self):

        ID = self.get_argument_int('screenshot_id', None)

        if not ID:
            return None, _('Give me screenshot_id please.')

        S = self.db.query(ApplianceScreenshot).get( ID )
        if not S:
            return None, _('Can not find screenshot %s') % ID

        if not ( S.appliance.user_id != self.current_user.id or
                 self.has_permission('admin') ):
            return None, _('No permission to manage screenshot')

        return S, None




class ScreenshotManagement(ScreenshotHandler):

    title = _('Add Screenshot For Appliance')
    template_path = 'appliance/screenshot_management.html'

    @authenticated
    def get(self):

        A, msg = self.get_appliance()
        if not A:
            return self.write( msg )

        self.prepare_kwargs['A'] = A
        self.prepare_kwargs['human_size'] = human_size

        self.render()



class ScreenshotAdd(ScreenshotHandler):

    title = _('Add Screenshot For Appliance')
    template_path = 'appliance/screenshot_add.html'

    @authenticated
    def prepare(self):

        A, msg = self.get_appliance()
        if not A:
            return self.write( msg )

        self.prepare_kwargs['A'] = A


    def get(self):
        self.render()

    def post(self):

        A = self.prepare_kwargs['A']

        if self.request.files:
            for f in self.request.files["logo"]:
                try:
                    # Size check
                    if len(f['body']) > settings.ATTACHMENT_MAXSIZE:
                        raise Exception(_('File is large than %s' % settings.ATTACHMENT_MAXSIZE))

                    S = ApplianceScreenshot( A, f )
                    self.db.add(S)
                    self.db.commit()

                except Exception, e:
                    return self.write( _('Upload screenshot failed: %s') % e )

        else:
            return self.write( _('No file find') )

        default_url = self.reverse_url('appliance:view') + '?id=%s' % A.id
        url = self.get_argument('next_url', default_url)
        self.redirect( url )



class ScreenshotDelete(ScreenshotHandler):

    @authenticated
    def get(self):

        S, msg = self.get_screenshot()
        if not S:
            return self.write( msg )

        AID = S.appliance_id

        try:
            self.db.delete( S )
            self.db.commit()

            # delete files
            for x in [ '%s-%s' % (S.checksum, S.filename),
                       '%s-thumb.png' % S.checksum ]:
                fn = os.path.join(S.base_path,  x)
                if os.path.exists( fn ):
                    os.unlink( fn )
        except Exception, e:
            logging.error('delete appliance screenshot failed: %s' % e)

        url = self.reverse_url('appliance:screenshot:management')
        url += '?appliance_id=%s' % AID
        self.redirect( url )
