from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship


class Node(ORMBase):

    __tablename__ = 'node'

    id = Column(Integer, Sequence('node_id_seq'), primary_key=True)

    hostname = Column( String(64) )

    key = Column( String(128) )
    ip = Column( String(32) )

    arch = Column( Integer ) # TODO: selected
    cpu_model = Column( Integer ) # TODO: selected , needed ?
    cpu_mhz = Column( Integer )

    status = Column( Integer ) # TODO: selected ?

    isenable = Column( Boolean ) # TODO: really needed ?
                                 # merge with status ?

    memory = Column( Integer ) # TODO: can selected ?
    cpus = Column( Integer )

    
    created = Column( DateTime )
    updated = Column( DateTime )


    def __init__(self, ip, arch):
        self.ip = ip
        self.arch = arch

    def __str__(self):
        return _("<Node(%s:%s)>") % (self.hostname, self.ip)

