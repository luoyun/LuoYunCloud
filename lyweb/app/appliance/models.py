import os
import logging
import Image
import tempfile
from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, BigInteger, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

import settings

from lytool.filesize import size as human_size

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

    created = Column( DateTime, default=datetime.now )
    updated = Column( DateTime, default=datetime.now )


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

    logoname = Column( String(64) )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref('appliances',order_by=id) )

    catalog_id = Column( ForeignKey('appliance_catalog.id') )
    catalog = relationship("ApplianceCatalog",backref=backref('appliances',order_by=id))

    filesize = Column( BigInteger )
    checksum = Column( String(32) ) # md5 value

    islocked = Column( Boolean, default = False) # Used by admin
    isuseable = Column( Boolean, default = True)
    isprivate = Column( Boolean, default = True)
    popularity = Column( Integer, default = 0 )

    created = Column( DateTime, default=datetime.now )
    updated = Column( DateTime, default=datetime.now )


    def __init__(self, name, user, filesize, checksum):
        self.name = name
        self.user_id = user.id
        self.filesize = filesize
        self.checksum = checksum

    def __unicode__(self):
        return "<Appliance(%s)>" % self.name

    @property
    def logourl(self):
        if os.path.exists(self.p_logo):
            return os.path.join(settings.STATIC_URL, 'appliance/%s/d.png' % self.id)
        else:
            return settings.APPLIANCE_LOGO_DEFAULT_URL

    @property
    def logodir(self):
        return os.path.join(settings.STATIC_PATH, 'appliance/%s' % self.id)

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

        if not os.path.exists(self.logodir):
            try:
                os.makedirs(self.logodir)
            except Exception, e:
                return _('create appliance logo dir "%(dir)s" failed: %(emsg)s') % {
                    'dir': self.logodir, 'emsg': e }

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
