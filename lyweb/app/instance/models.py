import os
import json
import logging
import datetime

from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

from app.auth.utils import enc_shadow_passwd
from app.site.models import SiteConfig

import settings


from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])


INSTANCE_STATUS_SHORT_STR = [
    ( 0, _('unknown') ),
    ( 1, _("new") ),
    ( 2, _('stop') ),
    ( 3, _('started') ),
    ( 4, _('osm connected') ),
    ( 5, _('service running') ),
    ( 9, _('suspend') ),
    ( settings.INSTANCE_DELETED_STATUS, _('deleted') ),
    ( 245, _('need query') ),
    ( 255, _('disk not exist') ) ]

INSTANCE_STATUS_CLASS = {
    0: ('#FFCC33', 'icon-exclamation-sign'),
    1: ('#999999', 'icon-cloud'),
    2: ('#CC0000', 'icon-off'),
    3: ('#99CCFF', 'icon-spinner icon-spin'),
    4: ('#6699FF', 'icon-spinner icon-spin'),
    5: ('#66CC00', 'icon-ok-sign'),
    9: ('red', 'icon-pause'),
    settings.INSTANCE_DELETED_STATUS: ('', 'icon-remove'),
    245: ('#FF9900', 'icon-question-sign'),
    255: ('#FF0000', 'icon-bolt'),
}


class Instance(ORMBase):

    _config_dict = {}

    __tablename__ = 'instance'

    id = Column( Integer, Sequence('instance_id_seq'), primary_key=True )

    name = Column( String(64) )
    key = Column( String(128) )
    summary = Column( String(1024) )
    description = Column( Text() )
    logo = Column( String(64) )

    cpus = Column( Integer, default=0 )
    memory = Column( Integer, default=0 )

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

    islocked = Column( Boolean, default = False) # Used by admin
    isprivate = Column( Boolean, default = True )
    ischanged = Column( Boolean, default = False )

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

    lastjob_id = Column( ForeignKey('job.id') )
    lastjob = relationship("Job")

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

    def __unicode__(self):
        return self.name


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
            255: _('the instance disk does not exist'),
        }

        return INSTANCE_STATUS_STR.get( self.status, _('Unknown Status') )

    @property
    def lastjob_status_string(self):
        if self.lastjob:
            return self.lastjob.status_string
        return ''

    @property
    def lastjob_status_id(self):
        if self.lastjob:
            return self.lastjob.status
        else:
            return 9999

    @property
    def lastjob_status_icon(self):
        if self.lastjob:
            return self.lastjob.status_icon
        else:
            return ''


    @property
    def is_running(self):
        return self.status in [3, 4, 5]

    @property
    def need_query(self):
        return self.status in [245, 255]


    def home_url(self, user=None, useip=None):

        if useip:
            host = self.ip
        else:
            host = self.domain if self.domain else self.ip

        if user and user.id == self.user_id and self.config:
            cookie = json.loads(self.config).get('cookie')
            if cookie:
                return "http://%s:8080/index.html?cookie=%s" % (host, cookie)

        return "http://%s:8080/index.html" % host


    @property
    def domain(self):

        for D in self.domains:
            return D.domain

        return self.default_domain


    @property
    def access_ip(self):
        ''' get the working ip '''

        ip = None

        if self.is_running and self.ip and self.ip != '0.0.0.0':
            return self.ip

        for IP in self.ips:
            return IP.ip

        return ip


    @property
    def work_ip(self):
        if self.is_running and self.ip and self.ip != '0.0.0.0':
            return self.ip
        else:
            return ''

    @property
    def description_html(self):
        return YMK.convert( self.description )

    @property
    def logourl(self):
        # TODO: use application logo default
        if not self.logo:
            return self.appliance.logourl

        if os.path.exists(self.logopath):
            return os.path.join(settings.STATIC_URL, 'instance/%s/%s' % (self.id, settings.INSTANCE_LOGO_NAME))
        else:
            return settings.INSTANCE_LOGO_DEFAULT_URL


    @property
    def logodir(self):
        return os.path.join(settings.STATIC_PATH, 'instance/%s' % self.id)

    @property
    def logopath(self):
        return os.path.join( self.logodir, settings.INSTANCE_LOGO_NAME )


    # TODO: a temp hack
    # key format =>  key:vdi_port:rx_bytes:rx_pkts:tx_bytes:tx_pkts
    @property
    def vdi_port(self):
        if not self.key: return 'None'
        port = self.key.split(':')
        return port[1] if len(port) >= 2 else 'None'

    @property
    def vdi_ip(self):
        if not self.node or not self.is_running: return 'None'
        return self.node.ip if hasattr(self.node, 'ip') else 'None'

    @property
    def rx_bytes(self):
        if not self.key: return 0
        rx = self.key.split(':')
        rx = rx[2] if len(rx) >= 3 else 0
        try:
            return int(rx)
        except:
            return 0

    @property
    def tx_bytes(self):
        if not self.key: return 0
        tx = self.key.split(':')
        tx = tx[4] if len(tx) >= 5 else 0
        try:
            return int(tx)
        except:
            return 0


    @property
    def status_icon(self):
        # a class for bootstrap style

        color, _class =  INSTANCE_STATUS_CLASS.get(
            self.status, ('red', 'icon-exclamation-sign'))

        return '<i style="color: %s;" class="%s"></i>' % (
            color, _class )

        
    def get(self, name, default=None):

        if not self._config_dict:
            self._config_dict = json.loads(self.config) if self.config else {}

        return self._config_dict.get(name, default)


    def set(self, item, value):

        config = json.loads(self.config) if self.config else {}
        config[item] = value

        self.config = json.dumps(config)
        self._config_dict = config
        self.updated = datetime.datetime.now()

    def delete(self, item):
        config = json.loads(self.config) if self.config else {}
        if item in config:
            del config[item]

            self.config = json.dumps(config)
            self._config_dict = config
            self.updated = datetime.datetime.now()

    def update_network(self):
        # TODO: support multi-network
        network = []
        nameservers = ""
        domain = self.get('domain', {})
        domain['ip'] = ''

        for ip in self.ips:
            network.append({
                    "ip": ip.ip,
                    "mac": self.mac,
                    "type": "default",
                    "netmask": ip.network.netmask,
                    "gateway": ip.network.gateway,
                    "nameservers": ip.network.nameservers,
                    })
            # TODO
            if ip.network.nameservers:
                nameservers = ip.network.nameservers

            # TODO

            domain['ip'] = ip.ip
            domain['name'] = self.domain

        self.set('network', network)
        self.set('nameservers', nameservers)
        self.set('domain', domain)

        if self.is_running:
            self.ischanged = True

        self.updated = datetime.datetime.now()


    def update_storage(self):

        storage = []

        for S in self.storages:

            storage.append({
                    "type": "disk",
                    "size": S.size,
                    })

        if storage:
            self.set('storage', storage)
        else:
            self.delete('storage')

    def set_root_password(self, password):
        root_passwd = enc_shadow_passwd( password )
        self.set('passwd_hash', root_passwd)


    @property
    def storage(self):
        s = 0
        for S in self.storages:
            s += S.size

        return s

    @property
    def use_global_passwd(self):
        return self.get('use_global_passwd', True)


    @property
    def default_domain(self):
        domain = settings.runtime_data.get('domain', None)
        if not domain:
            return ''
            
        top = domain.get('topdomain')
        prefix = domain.get('prefix')
        suffix = domain.get('suffix')
        return '%s%s%s.%s' % (prefix, self.id, suffix, top)

    @property
    def action(self):
        ''' Which action can do for this instance. '''

        a = 'stop'

        if not self.is_running:
            a = 'run'
        elif self.need_query:
            a = 'query'

        return a


    @property
    def action_human(self):
        ''' Which action can do for this instance. '''

        a = _('Stop My Instance')

        if not self.is_running:
            a = _('Run My Instance')
        elif self.need_query:
            a = _('Query My Instance')

        return a

