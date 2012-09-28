import os, random
from hashlib import sha1

from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from app.account.models import User

import settings


class Attachment(ORMBase):

    __tablename__ = 'attachment'

    id = Column(Integer, Sequence('attachment_id_seq'), primary_key=True)

    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User", order_by = id)

    name = Column( String(512) )
    savename = Column( String(1030) )
    origname = Column( String(1024) )

    size = Column( Integer )
    checksum = Column( String(256) )
    description = Column( Text() )

    dtimes = Column( Integer, default=0 )

    created = Column( DateTime(), default=datetime.utcnow )
    updated = Column( DateTime() )


    def __init__(self, user, fileobj):
        self.user = user
        self.user_id = user.id
        self.save_file(fileobj)


    def __repr__(self):
        return _("[Attachment (%s)]") % self.id

    def __unicode__(self):
        return self.name

    @property
    def url(self):
        return '%s/%s/%s' % (settings.ATTACHMENT_URL.rstrip('/'),
                             self.user_id, self.savename)

    def save_file(self, fileobj):

        if not os.path.exists( settings.ATTACHMENT_PATH ):
            os.mkdir( settings.ATTACHMENT_PATH )

        USER_PATH = os.path.join(settings.ATTACHMENT_PATH, str(self.user_id))
        if not os.path.exists( USER_PATH ):
            os.mkdir( USER_PATH )

        origname = fileobj['filename']
        #fullname = self.get_fullname( origname )
        savename = '%s-%s' % (random.randint(1, 1000000), origname)
        fullname = os.path.join(USER_PATH, savename)

        sha1_obj = sha1()
        f = open(fullname, 'wb')
        f.write( fileobj['body'] )
        sha1_obj.update( fileobj['body'] )
        f.close()

        self.origname = origname
        self.savename = savename
        self.name = origname
        self.checksum = sha1_obj.hexdigest()

        self.size = os.path.getsize( fullname )

    def get_fullname(self, origname):

        suffix = self.get_suffix(origname)

        now = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
        savename = '.'.join([now, str(random.randint(1, 1000000)), suffix])

        return os.path.join(USER_PATH, savename)


    def get_suffix(self, origname):

        L = origname.split('.')

        # TODO: more type check

        if len(L) > 2:

            if len(L) > 3:
                suffix = '.'.join(L[-3:-1])
                if suffix in ['pkg.tar']:
                    return '.'.join(L[-3:])

            suffix = '.'.join(L[-2:])
            if suffix in ['tar.xz','tar.gz','tar.bz2']:
                return suffix

        return L.pop()
