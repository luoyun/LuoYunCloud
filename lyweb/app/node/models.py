from datetime import datetime
from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

from yweb.utils.filesize import size as human_size



class Node(ORMBase):

    __tablename__ = 'node'

    id = Column(Integer, Sequence('node_id_seq'), primary_key=True)

    hostname = Column( String(64) )

    key = Column( String(128) )
    ip = Column( String(32) )

    arch = Column( Integer ) # TODO: selected
    cpu_model = Column( String(64) )
    cpu_mhz = Column( Integer )

    status = Column( Integer ) # TODO: selected ?

    isenable = Column( Boolean ) # TODO: really needed ?
                                 # merge with status ?

    memory = Column( Integer )
    cpus = Column( Integer )

    vmemory = Column( Integer )
    vcpus = Column( Integer )
    
    created = Column( DateTime )
    updated = Column( DateTime )


    def __init__(self, ip, arch):
        self.ip = ip
        self.arch = arch

    def __str__(self):
        return "<Node(%s:%s)>" % (self.hostname, self.ip)

    @property
    def memory_human(self):
        try:
            return human_size(self.memory*1024)
        except:
            return ''

    @property
    def vmemory_human(self):
        try:
            return human_size(self.vmemory*1024)
        except:
            return ''
