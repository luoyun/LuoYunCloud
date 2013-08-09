#/usr/bin/env python2.5

import os, random, json
import logging
import datetime
from hashlib import sha1

from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from app.auth.utils import enc_shadow_passwd

from app.site.utils import get_site_config

import settings


class UserProfile(ORMBase):

    _config_dict = {}

    __tablename__ = 'user_profile'

    id = Column( Integer, Sequence('user_profile_id_seq'), primary_key=True )

    # one to one, add the 'uselist=False' in backref
    # http://docs.sqlalchemy.org/en/rel_0_8/orm/relationships.html#one-to-one
    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref(
            'profile', uselist=False, order_by=id) )

    # cloud coin, pay for resource
    coins = Column( Integer, default=0 )

    # resource
    cpu       = Column( Integer, default = 0 ) # core
    memory    = Column( Integer, default = 0 ) # MB
    storage   = Column( Integer, default = 0 ) # GB
    instance  = Column( Integer, default = 0 ) # Number
    bandwidth = Column( Integer, default = 0 ) # Mbps
    rx        = Column( Integer, default = 0 ) # G
    tx        = Column( Integer, default = 0 ) # G
    port      = Column( Integer, default = 0 ) # Number
    vlan      = Column( Integer, default = 0 ) # Number
    domain    = Column( Integer, default = 0 ) # Number

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

    # Other configure
    config = Column( Text() )


    def __init__(self, user):

        self.user_id = user.id

        self.cpu = get_site_config(
            'user.default.static_cpu', settings.USER_DEFAULT_CPU )

        self.memory = get_site_config(
            'user.default.static_memory', settings.USER_DEFAULT_MEMORY )

        self.storage = get_site_config(
            'user.default.static_storage', settings.USER_DEFAULT_STORAGE )

        self.instance = get_site_config(
            'user.default.static_instance', settings.USER_DEFAULT_INSTANCE )

        self.bandwidth = get_site_config(
            'user.default.static_bandwidth', settings.USER_DEFAULT_BANDWIDTH )

        self.rx = get_site_config(
            'user.default.static_rx', settings.USER_DEFAULT_RX )

        self.tx = get_site_config(
            'user.default.static_tx', settings.USER_DEFAULT_TX )

        self.port = get_site_config(
            'user.default.static_port', settings.USER_DEFAULT_PORT )

        self.vlan = get_site_config(
            'user.default.static_vlan', settings.USER_DEFAULT_VLAN )

        self.domain = get_site_config(
            'user.default.static_domain', settings.USER_DEFAULT_DOMAIN )


    def __repr__(self):
        return "UserProfile <%s>" % self.id


    def get_resource_total(self):

        d = { 'cpu': self.cpu,
              'memory': self.memory,
              'instance': self.instance,
              'storage': self.storage }

        now = datetime.datetime.now()

        for R in self.user.resources:
            if ( R.effect_date < now < R.expired_date ):

                if R.type == R.T_CPU:
                    d['cpu'] += R.size

                elif R.type == R.T_MEMORY:
                    d['memory'] += R.size

                elif R.type == R.T_STORAGE:
                    d['storage'] += R.size

                elif R.type == R.T_INSTANCE:
                    d['instance'] += R.size

        return d


    def get_resource_used(self):

        d = { 'cpu': 0,
              'memory': 0,
              'instance': 0,
              'storage': 0 }

        for I in self.user.instances:

            if I.is_running:
                d['cpu'] += I.cpus
                d['memory'] += I.memory

            d['instance'] += 1

            for S in I.storages:
                d['storage'] += S.size

        return d


    @property
    def cpu_remain(self):

        total = self.cpu
        used = 0

        now = datetime.datetime.now()

        for R in self.user.resources:
            if ( R.type == R.T_CPU and
                 R.effect_date < now < R.expired_date ):
                total += R.size

        for I in self.user.instances:
            if I.is_running:
                used += I.cpus

        return total - used if total > used else 0


    @property
    def memory_remain(self):

        total = self.memory
        used = 0

        now = datetime.datetime.now()

        for R in self.user.resources:
            if ( R.type == R.T_MEMORY and
                 R.effect_date < now < R.expired_date ):
                total += R.size

        for I in self.user.instances:
            if I.is_running:
                used += I.memory

        return total - used if total > used else 0


    @property
    def storage_remain(self):

        total = self.storage
        used = 0

        now = datetime.datetime.now()

        for R in self.user.resources:
            if ( R.type == R.T_STORAGE and
                 R.effect_date < now < R.expired_date ):
                total += R.size

        for I in self.user.instances:
            for S in I.storages:
                used += S.size

        return total - used if total > used else 0


    @property
    def instance_remain(self):

        used = len(self.user.instances)
        total = self.instance

        now = datetime.datetime.now()

        for R in self.user.resources:
            if ( R.type == R.T_INSTANCE and
                 R.effect_date < now < R.expired_date ):
                total += R.size

        return total - used if total > used else 0


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

    def set_root_password(self, password):
        root_passwd = enc_shadow_passwd( password )
        self.set('secret', { "root_shadow_passwd": root_passwd })

    def get_root_password(self):

        secret = self.get('secret', {})
        if isinstance(secret, dict):
            return secret.get('root_shadow_passwd', None)

        return None
            


class UserResetpass(ORMBase):

    ''' reset password apply '''

    __tablename__ = 'user_resetpass'

    id = Column(Integer, Sequence('user_resetpass_id_seq'), primary_key=True)

    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User", order_by = id)

    key = Column( String(128) )

    created  = Column( DateTime(), default=datetime.datetime.now )
    completed  = Column( DateTime() )


    def __init__(self, user):
        self.key = sha1(str(random.random())).hexdigest()
        self.user = user
        self.user_id = user.id


    def __repr__(self):
        return _("[User reset password apply (%s)]") % self.id



class PublicKey(ORMBase):

    __tablename__ = 'public_key'

    _config_dict = {}

    id = Column( Integer, Sequence('public_key_id_seq'), primary_key=True )

    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref('keys', order_by=id))

    name = Column( String(128) )
    data = Column( String(1024) )

    isdefault = Column( Boolean, default = False)

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

    def __init__(self, user, name, key):
        self.user_id = user.id
        self.name = name
        self.data = key

        isdefault = False
        for K in user.keys:
            if K.isdefault:
                isdefault = True

        self.isdefault = not isdefault


    def set_default(self):
        for K in self.user.keys:
            if K.isdefault:
                K.isdefault = False
        self.isdefault = True
