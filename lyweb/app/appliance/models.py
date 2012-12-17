import os, logging
from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, BigInteger, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

import settings

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
        if os.path.exists(self.logothum):
            return os.path.join(settings.STATIC_URL, 'appliance/%s/%s' % (self.id, settings.APPLIANCE_LOGO_THUM_NAME))
        else:
            return settings.APPLIANCE_LOGO_DEFAULT_URL

    @property
    def logodir(self):
        return os.path.join(settings.STATIC_PATH, 'appliance/%s' % self.id)

    @property
    def logopath(self):
        return os.path.join(self.logodir, settings.APPLIANCE_LOGO_NAME)

    @property
    def logothum(self):
        return os.path.join(self.logodir, settings.APPLIANCE_LOGO_THUM_NAME)

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
