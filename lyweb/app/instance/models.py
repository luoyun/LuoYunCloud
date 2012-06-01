import os

from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Text, ForeignKey

from sqlalchemy.orm import backref,relationship

import settings


class Instance(ORMBase):

    __tablename__ = 'instance'

    id = Column( Integer, Sequence('instance_id_seq'), primary_key=True )

    name = Column( String(64) )
    key = Column( String(128) )
    summary = Column( String(1024) )
    description = Column( Text() )
    logo = Column( String(64) )

    cpus = Column( Integer, default=1 )
    memory = Column( Integer, default=256 )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref('instances',order_by=id) )

    appliance_id = Column( ForeignKey('appliance.id') )
    appliance = relationship("Appliance",backref=backref('instances',order_by=id) )

    node_id = Column( ForeignKey('node.id') )
    node = relationship("Node",backref=backref('instances', order_by=id) )

    ip = Column( String(32) )
    mac = Column( String(32) )

    status = Column( Integer, default=1 )
    config = Column( String(256) ) # TODO

    created = Column( DateTime, default=datetime.utcnow() )
    updated = Column( DateTime, default=datetime.utcnow() )


    def __init__(self, name, user, appliance):
        self.name = name
        self.user_id = user.id
        self.appliance_id = appliance.id


    def __str__(self):
        return _("<Instance(%s)>") % self.name


    # TODO: have a lazy translation
    @property
    def status_string(self):

        INSTANCE_STATUS_STR = {
            0: _('unknown'),
            1: _("new domain that hasn't run once"),
            2: _('stopped'),
            3: _('started by hypervisor'),
            4: _('osm connected'),
            5: _('application is running'),
            9: _('suspend'),
            245: _('needs queryed'),
            255: _('not exist'),
        }

        return INSTANCE_STATUS_STR.get( self.status, _('Unknown') )

    @property
    def logo_url(self):

        logoname = self.logo

        p = os.path.join( settings.STATIC_PATH,
                          'instance_logo/%s' % logoname )
        if not os.path.exists(p):
            logoname = 'default.png'

        return '%s%s' % (
            '/static/instance_logo/', logoname )


    # TODO: stop and run check should merge
    #       should check more ? 
    @property
    def can_stop(self):
        return self.status in [0, 3, 4, 5, 9, 245]

    @property
    def can_run(self):
        return self.status in [1, 2]

    @property
    def is_running(self):
        return self.status in [4, 5]


    @property
    def home_url(self):
        return "/proxy?host=%s&port=8080" % self.ip
        #return "http://%s:8080" % self.ip

