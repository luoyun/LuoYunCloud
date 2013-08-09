import datetime

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from yweb.orm import ORMBase


class StoragePool(ORMBase):

    '''Storage Pool'''

    __tablename__ = 'storagepool'

    id = Column( Integer, Sequence('storagepool_id_seq'), primary_key=True )

    name = Column( String(128) )
    description = Column( Text() )

    total = Column( Integer, default=0 ) # max size
    used = Column( Integer, default=0 )  # used size

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

    def __unicode__( self ):
        return self.name

    @property
    def remain(self):
        return self.total - self.used

    def update_used(self):

        used = 0

        for S in self.storages:
            used += S.size

        self.used = used


class Storage(ORMBase):

    __tablename__ = 'storage'

    id = Column( Integer, Sequence('storage_id_seq'), primary_key=True )

    size = Column( Integer, default=0 )

    pool_id = Column( ForeignKey('storagepool.id') )
    pool = relationship("StoragePool", backref=backref('storages', order_by=id))

    instance_id = Column( ForeignKey('instance.id') )
    instance = relationship("Instance", backref=backref('storages', order_by=id))

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )


    def __init__(self, size, pool, instance):

        if pool.remain > size:
            self.size = size
            
        else:
            self.size = pool.remain

        # TODO: update used
        #pool.used += self.size

        self.pool_id = pool.id
        self.instance_id = instance.id
