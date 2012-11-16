from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from ytime import htime, ftime


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

    created = Column( DateTime, default=datetime.now )
    updated = Column( DateTime, default=datetime.now )


    def __init__(self, ip, user, instance=None):
        self.ip = ip
        self.user_id = user.id
        if instance:
            self.instance_id = instance.id



class NetworkPool(ORMBase):

    __tablename__ = 'networkpool'

    id = Column( Integer, Sequence('networkpool_id_seq'), primary_key=True )

    name = Column( String(128) )
    description = Column( Text() )

    start = Column( String(60) )
    end = Column( String(60) )
    netmask = Column( String(60) )
    gateway = Column( String(60) )
    nameservers = Column( String(1024) )
    exclude_ips = Column( Text() )

    created = Column( DateTime, default=datetime.now )
    updated = Column( DateTime, default=datetime.now )

    def __init__( self, name, description = None,
                  start = None, end = None,
                  netmask = None, gateway = None,
                  nameservers = None, exclude_ips = None ):
        self.name = name
        self.description = description
        self.start = start
        self.end = end
        self.netmask = netmask
        self.gateway = gateway
        self.nameservers = nameservers
        self.exclude_ips = exclude_ips

    def __unicode__( self ):
        return self.name



class IPPool(ORMBase):

    __tablename__ = 'ippool'

    id = Column( Integer, Sequence('ippool_id_seq'), primary_key=True )
    ip = Column( String(60),  unique = True )

    network_id = Column( ForeignKey('networkpool.id') )
    network = relationship("NetworkPool", backref=backref('ips', order_by=id))

    instance_id = Column( ForeignKey('instance.id') )
    instance = relationship("Instance", backref=backref('ips', order_by=id))

    created = Column( DateTime, default=datetime.now )
    updated = Column( DateTime, default=datetime.now )


    def __init__(self, ip, network):

        self.ip = ip
        self.network_id = network.id



class LyTrace(ORMBase):

    __tablename__ = 'lytrace'

    id = Column( Integer, Sequence('lytrace_id_seq'), primary_key=True )

    who_id = Column( ForeignKey('auth_user.id') )
    who = relationship("User", backref=backref('traces', order_by=id))

    when = Column( DateTime, default=datetime.now )
    comefrom = Column( String(512) )    # ip
    agent = Column( String(1024) )  # browser
    visit = Column( String(1024) )

    target_type = Column( Integer )
    target_id = Column( Integer )

    do = Column( String(1024) )
    isok = Column( Boolean, default = False) # result status
    result = Column( String(1024) )

    def __init__(self, who, comefrom, agent, visit):
        self.who_id = who.id
        self.comefrom = comefrom
        self.agent = agent
        self.visit = visit

    def __unicode__(self):
        return _('%s: %s come from %s do "%s" , %s') % (
            ftime(self.when), self.who.username, self.comefrom,
            self.do, self.isok)
