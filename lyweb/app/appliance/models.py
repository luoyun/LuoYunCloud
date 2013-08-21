import os
import logging
import Image
import tempfile
import datetime
from hashlib import sha1
from yweb.orm import ORMBase

from sqlalchemy import Column, BigInteger, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

from app.site.utils import get_site_config

import settings
from app.system.utils import get_runtime_data

from yweb.utils.filesize import size as human_size
from yweb.utils.base import makesure_path_exist

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])



class ApplianceCatalog(ORMBase):

    __tablename__ = 'appliance_catalog'

    id = Column( Integer, Sequence('appliance_catalog_id_seq'), primary_key=True )

    name = Column( String(64) )
    summary = Column( String(1024) )
    description = Column( Text() )

    position = Column( Integer, default = 0 )

    # TODO:  is self only ?! can used by myself !

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )


    def __init__(self, name, summary='', description=''):
        self.name = name
        self.summary = summary
        self.description = description

    def __unicode__(self):
        return '<Catalog(%s)>' % self.name

    @property
    def description_html(self):
        return YMK.convert( self.description )


OSType = [
    (1, _('GNU/Linux')),
    (2, _('Microsoft Windows'))
]

class Appliance(ORMBase):

    __tablename__ = 'appliance'

    id = Column(Integer, Sequence('appliance_id_seq'), primary_key=True)

    name = Column( String(128) )
    summary = Column( String(1024) )
    description = Column( Text() )

    os = Column( Integer(), default = 1 ) # 1 is gnu/linux
    disksize = Column( BigInteger ) # disk size used by appliance
    disktype = Column( Integer )    # raw, qcow2

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref('appliances',order_by=id) )

    catalog_id = Column( ForeignKey('appliance_catalog.id') )
    catalog = relationship("ApplianceCatalog",backref=backref('appliances',order_by=id))

    filesize = Column( BigInteger )
    checksum = Column( String(32) ) # md5 value

    islocked  = Column( Boolean, default = False) # Used by admin
    isuseable = Column( Boolean, default = True)
    isprivate = Column( Boolean, default = True)

    like   = Column(Integer, default=0)
    unlike = Column(Integer, default=0)
    visit  = Column(Integer, default=0) # view times

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )


    def __init__(self, name, user, filesize, checksum):
        self.name = name
        self.user_id = user.id
        self.filesize = filesize
        self.checksum = checksum


    def __unicode__(self):
        return "<Appliance(%s)>" % self.name


    @property
    def logourl(self):

        if not os.path.exists(self.p_logo):
            return settings.APPLIANCE_LOGO_DEFAULT_URL

        base_url = get_runtime_data('site.download.base_url', '/dl/')

        return '%s/appliance/%s/d.png' % (
            base_url.rstrip('/'), self.id )


    @property
    def logodir(self):

        upload_dir = get_runtime_data('site.upload.base_dir', '/opt/LuoYun/data/')

        path = '%s/appliance/%s/' % (
            upload_dir.rstrip('/'), self.id )

        return path


    @property
    def p_logo(self):
        ''' Appliance default logo path'''
        return os.path.join(self.logodir, 'd.png')

    @property
    def p_logo_raw(self):
        ''' Appliance raw logo path '''
        return os.path.join(self.logodir, 'r.png')

    def rebuild_logo(self):
        ''' Generate relative file and type of logo '''

        self._rebuild_default_logo()

    def _rebuild_default_logo(self):
        ''' Paste raw image to default logo '''

        left = 14
        top = 7
        width = 160
        height = 160

        box = (left, top, left + width, top + height)

        fg = Image.open(self.p_logo_raw)
        fg = fg.resize((width, height))

        border_path = os.path.join(settings.STATIC_PATH, 'image/appliance_border.png')
        border = Image.open(border_path)
        source = border.convert('RGB')
        fg.paste(source, mask=border)

        bg_path = os.path.join(settings.STATIC_PATH, 'image/appliance_bg.jpg')
        bg = Image.open(bg_path)
        bg.paste(fg, box)
        bg.save(self.p_logo)

    def save_logo(self, request_files):
        ''' save logo file
        request_files = self.request.files['logo']
        '''

        if not makesure_path_exist( self.logodir ):
            return _('create appliance logo dir "%s" failed') % self.logodir

        max_size = settings.APPLIANCE_LOGO_MAXSIZE

        for f in request_files:

            if len(f['body']) > max_size:
                return self.trans(_('Picture must smaller than %s !')) % human_size(max_size)

            tf = tempfile.NamedTemporaryFile()
            tf.write(f['body'])
            tf.seek(0)

            try:
                img = Image.open(tf.name)
            except Exception, emsg:
                return _('Open %(filename)s failed: %(emsg)s , is it a picture ?') % {
                    'filename': f.get('filename'), 'emsg': emsg }

            try:
                # can convert image type
                img.save(self.p_logo_raw)

            except Exception, emsg:
                return _('Save %(filename)s failed: %(emsg)s') % {
                    'filename': f.get('filename'), 'emsg': emsg }

            self._rebuild_default_logo()                
            tf.close()


    @property
    def description_html(self):
        return YMK.convert( self.description )

    @property
    def catalog_name(self):
        if self.catalog:
            return self.catalog.name
        else:
            return _('None')

    @property
    def download_url(self):
        return os.path.join(settings.appliance_top_url, 'appliance_%s' % self.checksum)



class ApplianceScreenshot(ORMBase):

    __tablename__ = 'appliance_screenshot'

    id = Column(Integer, Sequence('appliance_screenshot_id_seq'), primary_key=True)

    appliance_id = Column( Integer, ForeignKey('appliance.id') )
    appliance = relationship("Appliance", backref=backref('screenshots'))

    filename = Column( String(1024) )
    size = Column( Integer )
    checksum = Column( String(256) )

    like   = Column( Integer, default=0 )
    unlike = Column( Integer, default=0 )
    visit  = Column( Integer, default=0 )

    updated = Column( DateTime(), default=datetime.datetime.now )
    created = Column( DateTime(), default=datetime.datetime.now )


    def __init__(self, appliance, fileobj):
        self.appliance_id = appliance.id
        self.save_file(fileobj)


    @property
    def url(self):

        savename = '%s-%s' % (self.checksum, self.filename)

        base_url = get_runtime_data('site.download.base_url', '/dl/')

        return '%s/appliance/%s/screenshot/%s' % (
            base_url.rstrip('/'), self.appliance_id, savename )

    @property
    def thumb_url(self):

        savename = '%s-thumb.png' % self.checksum

        base_url = get_runtime_data('site.download.base_url', '/dl/')

        return '%s/appliance/%s/screenshot/%s' % (
            base_url.rstrip('/'), self.appliance_id, savename )


    @property
    def base_path(self):
        upload_dir = get_runtime_data('site.upload.base_dir', '/opt/LuoYun/data/')
        path = '%s/appliance/%s/screenshot/' % (
            upload_dir.rstrip('/'), self.appliance_id )

        return path


    def save_file(self, fileobj):

        upload_dir = get_runtime_data('site.upload.base_dir', '/opt/LuoYun/data/')

        path = '%s/appliance/%s/screenshot/' % (
            upload_dir.rstrip('/'), self.appliance_id )

        if not makesure_path_exist( path ):
            return _('makesure_path_exist failed.')

        sha1_obj = sha1()
        sha1_obj.update( fileobj['body'] )

        checksum = sha1_obj.hexdigest()
        filename = fileobj['filename']

        savename = '%s-%s' % (checksum, filename)
        fullname = os.path.join(path, savename)

        f = open(fullname, 'wb')
        f.write( fileobj['body'] )
        f.close()

        try:
            thumbname = '%s-thumb.png' % checksum
            fullthumb = os.path.join(path, thumbname)

            img = Image.open(fullname)

            img.thumbnail((800, 500), Image.ANTIALIAS)
            img.save( fullthumb )
        except:
            pass

        self.filename = filename
        self.checksum = checksum
        self.size     = os.path.getsize( fullname )

