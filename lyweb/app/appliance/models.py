from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

import settings



class ApplianceCatalog(ORMBase):

    __tablename__ = 'appliance_catalog'

    id = Column( Integer, Sequence('appliance_catalog_id_seq'), primary_key=True )

    name = Column( String(64) )
    summary = Column( String(1024) )
    description = Column( Text() )

    position = Column( Integer, default = 0 )

    # TODO:  is self only ?! can used by myself !

    created = Column( DateTime, default=datetime.utcnow() )
    updated = Column( DateTime, default=datetime.utcnow() )


    def __init__(self, name, summary='', description=''):
        self.name = name
        self.summary = summary
        self.description = description

    def __repr__(self):
        return _("[Catalog(%s)]") % self.name



class Appliance(ORMBase):

    __tablename__ = 'appliance'

    id = Column(Integer, Sequence('appliance_id_seq'), primary_key=True)

    name = Column( String(128) )
    summary = Column( String(1024) )
    description = Column( Text() )

    logoname = Column( String(64) )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref('appliances',order_by=id) )

    catalog_id = Column( ForeignKey('appliance_catalog.id') )
    catalog = relationship("ApplianceCatalog",backref=backref('appliances',order_by=id))

    filesize = Column( Integer )
    checksum = Column( String(32) ) # md5 value

    isuseable = Column( Boolean, default = True)
    isprivate = Column( Boolean, default = True)
    popularity = Column( Integer, default = 0 )

    created = Column( DateTime, default=datetime.utcnow() )
    updated = Column( DateTime, default=datetime.utcnow() )


    def __init__(self, name, user, filesize, checksum):
        self.name = name
        self.user_id = user.id
        self.filesize = filesize
        self.checksum = checksum

    def __repr__(self):
        return _("[Appliance(%s)]") % self.name


    @property
    def logo_url(self):

        if hasattr(self, 'logoname') and self.logoname:
            return '%s%s' % (
                settings.appliance_top_url,
                self.logoname)
        else:
            return '%simg/appliance.png' % settings.THEME_URL
