import datetime
from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref


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

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

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

    def get_free_ip(self):
        for IP in self.ips:
            if not IP.instance_id:
                return IP

        return None


class IPPool(ORMBase):

    __tablename__ = 'ippool'

    id = Column( Integer, Sequence('ippool_id_seq'), primary_key=True )
    ip = Column( String(60),  unique = True )

    network_id = Column( ForeignKey('networkpool.id') )
    network = relationship("NetworkPool", backref=backref('ips', order_by=id))

    instance_id = Column( ForeignKey('instance.id') )
    instance = relationship("Instance", backref=backref('ips', order_by=id))

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )


    def __init__(self, ip, network):

        self.ip = ip
        self.network_id = network.id



class Gateway(ORMBase):

    __tablename__ = 'gateway'

    id = Column( Integer, Sequence('gateway_id_seq'), primary_key=True )

    name = Column( String(128) )
    description = Column( Text() )

    ip      = Column( String(60),  unique = True )
    netmask = Column( String(60) )

    start = Column( Integer ) # start port
    end = Column( Integer )   # end port
    exclude_ports = Column( Text() )

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )


    def get_free_port(self):
        for P in self.ports:
            if not (P.ip_port or P.ip_id):
                return P

        return None



class PortMapping(ORMBase):

    __tablename__ = 'port_mapping'

    id = Column( Integer, Sequence('port_mapping_id_seq'), primary_key=True )

    gateway_port  = Column( Integer )
    gateway_id = Column( ForeignKey('gateway.id') )
    gateway = relationship("Gateway", backref=backref('ports', order_by=id))

    ip_port  = Column( Integer )
    ip_id = Column( ForeignKey('ippool.id') )
    ip = relationship("IPPool", backref=backref('ports', order_by=id))

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

