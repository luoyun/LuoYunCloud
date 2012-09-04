import os, json

from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

import settings

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])


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
    config = Column( Text() ) # Other configure

    isprivate = Column( Boolean, default = True )
    ischanged = Column( Boolean, default = False )

    created = Column( DateTime, default=datetime.utcnow() )
    updated = Column( DateTime, default=datetime.utcnow() )

    subdomain = Column( String(32), unique = True )


    def __init__(self, name, user, appliance):
        self.name = name
        self.user_id = user.id
        self.appliance_id = appliance.id
        self.init_config()


    def init_config(self):
        # Set a cookie
        import random, time
        from hashlib import sha1
        session_key = sha1('%s%s' % (random.random(), time.time())).hexdigest()
        self.config = json.dumps( {
                'cookie': session_key,
                'webssh': { 'status': 'enable',
                            'port': 8001 }
                } )

    def __str__(self):
        return _("<Instance(%s)>") % self.name


    # TODO: have a lazy translation
    @property
    def status_string(self):

        INSTANCE_STATUS_STR = {
            0: _('unknown'),
            1: _("new instance that hasn't run once"),
            2: _('instance is stopped'),
            3: _('instance is started by hypervisor'),
            4: _('osm in instance connected'),
            5: _('application is running'),
            9: _('instance is suspend'),
            settings.INSTANCE_DELETED_STATUS: _('instance is deleted'),
            245: _('instance needs queryed'),
            255: _('instance is not exist'),
        }

        return INSTANCE_STATUS_STR.get( self.status, _('Unknown Status') )

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
        return self.status in [3, 4, 5]


    def home_url(self, user=None):

        host = self.domain if self.domain else self.ip

        if user and user.id == self.user_id and self.config:
            cookie = json.loads(self.config).get('cookie')
            if cookie:
                return "http://%s:8080/index.html?cookie=%s" % (host, cookie)

        return "http://%s:8080/index.html" % host


    @property
    def domain(self):
        if self.config:
            config = json.loads(self.config)
            if 'domain' in config.keys():
                domain = config['domain']
                if 'name' in domain.keys():
                    return domain['name']
        return None


    @property
    def access_ip(self):
        ''' get the working ip '''

        ip = None

        if self.is_running and self.ip:
            ip = self.ip

        if not ip:
            config = json.loads(self.config)
            if 'network' in config.keys():
                network = config['network'][0]
                if 'ip' in network.keys():
                    ip = network['ip']

        return ip


    @property
    def storage(self):
        config = json.loads(self.config)
        if 'storage' in config.keys():
            storage = config['storage'][0]
            return int(storage.get('size', 0))

        return 0


    @property
    def description_html(self):
        return YMK.convert( self.description )
