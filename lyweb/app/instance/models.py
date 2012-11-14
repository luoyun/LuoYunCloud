import os, json, logging

from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Text, ForeignKey, Boolean

from sqlalchemy.orm import backref,relationship

import settings

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])


import Image
from yimage import watermark


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

    islocked = Column( Boolean, default = False) # Used by admin
    isprivate = Column( Boolean, default = True )
    ischanged = Column( Boolean, default = False )

    created = Column( DateTime, default=datetime.now )
    updated = Column( DateTime, default=datetime.now )

    lastjob_id = Column( ForeignKey('job.id') )
    lastjob = relationship("Job")

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

    def get_network_count(self):
        config = json.loads( self.config )
        network = config.get('network', [])
        return len(network)

    def get_network(self, index=1):
        config = json.loads( self.config )
        network = config.get('network', [])
        count = len(network)
        if index > count or index < 1:
            return {}

        return network[index-1]


    def set_network(self, nic_config, index=1):
        config = json.loads( self.config )
        network = config.get('network', [])

        if network:
            count = len(network)
            if index < 1:
                return False
            elif index <= count:
                network[index-1] = nic_config
            else:
                network.append(nic_config)
        else:
            network = [nic_config]

        config['network'] = network
        self.config = json.dumps(config)

        # TODO: set status change flag
        if self.is_running:
            self.ischanged = True

        return True

    def clean_network(self, index):
        config = json.loads( self.config )
        network = config.get('network', [])
        count = len(network)
        if index > count or index < 1:
            return False

        if index == 1:
            ip = network[0].get('ip')
            if ip:
                for x in self.ips:
                    if ip == x.ip:
                        x.instance_id = None
                        x.updated = datetime.now()
                        break

            network[0] = {'type': 'default', 'mac': self.mac}

        else:
            del network[index-1]

        config['network'] = network
        self.config = json.dumps(config)

        # TODO: set status change flag
        if self.is_running:
            self.ischanged = True

        return True


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
    def job_status_string(self):
        if self.lastjob:
            return self.lastjob.status_string
        else:
            return ''

    @property
    def lastjob_status_id(self):
        if self.lastjob:
            return self.lastjob.status
        else:
            return ''

    @property
    def lastjob_imgurl(self):
        if self.lastjob:
            if self.lastjob.completed:
                if self.lastjob.status >= 600:
                    return '%s.png' % self.lastjob.id
                else:
                    return 'completed.png'
            else:
                return 'running.gif'
        else:
            return 'nojob.png'
        

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

    @property
    def need_query(self):
        return self.status in [245, 255]


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
    def work_ip(self):
        if self.is_running and self.ip and self.ip != '0.0.0.0':
            return self.ip
        else:
            return ''


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

    @property
    def logourl(self):

        # TODO: hack !!!
        if not os.path.exists(self.logopath):
            import Image
            #old = '/opt/LuoYun/web/static/instance_logo/%s' % self.logo
            old = '/opt/LuoYun/data/appliance/%s' % self.appliance.logoname
            if os.path.exists(old):
                try:
                    if not os.path.exists(self.logodir):
                        os.makedirs(self.logodir)

                    img = Image.open( old )
                    img.save( self.logopath )
                except Exception, msg:
                    logging.error('resave instance %s logo failed: %s' % (self.id, msg))

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

    def save_logo(self):
        ''' Create logo '''

        if not os.path.exists(self.appliance.logothum):
            return logging.warning('appliance %s has not logo.' % self.appliance_id)

        # make sure dir is exist
        if not os.path.exists(self.logodir):
            try:
                os.makedirs(self.logodir)
            except Exception, e:
                return logging.error('create instance logo dir "%s" failed: %s' % (self.logodir, e))


        try:

            I = Image.open(self.appliance.logothum)

            if os.path.exists(settings.INSTANCE_LOGO_MARK):
                M = Image.open(settings.INSTANCE_LOGO_MARK)
                position = ( (I.size[0] - M.size[0]) / 2,
                             I.size[1] - M.size[1] )
                img = watermark(I, M, position, 0.3)
                img.save( self.logopath )
            else:
                I.save( self.logopath )

        except Exception, e:

            logging.error('create instance logo failed: %s' % e)

