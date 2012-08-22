from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref



class LuoYunConfig(ORMBase):

    ''' This is a config style against unix

    Use DB, not text file.
    '''

    __tablename__ = 'configure'

    id = Column(Integer, Sequence('auth_session_id_seq'), primary_key=True)
    key  = Column( String(40) )
    value = Column( Text() )
    description  = Column( Text() )


    def __init__(self, key, value):
        self.key = key
        self.value = value


    def __repr__(self):
        return _("[LuoYun(%s=%s)]") % (self.key, self.value)




class IpAssign(ORMBase):

    __tablename__ = 'ip_assign'

    id = Column( Integer, Sequence('ip_assign_id_seq'), primary_key=True )

    ip = Column( String(32) )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User", backref=backref('static_ips',order_by=id) )

    instance_id = Column( ForeignKey('instance.id') )
    instance = relationship("Instance", backref=backref('static_ips', order_by=id))

    created = Column( DateTime, default=datetime.utcnow() )
    updated = Column( DateTime, default=datetime.utcnow() )


    def __init__(self, ip, user, instance=None):
        self.ip = ip
        self.user_id = user.id
        if instance:
            self.instance_id = instance.id
