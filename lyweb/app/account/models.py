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

import settings



class UserProfile(ORMBase):

    __tablename__ = 'user_profile'

    _config_dict = {}

    id = Column( Integer, Sequence('user_profile_id_seq'), primary_key=True )

    # one to one, add the 'uselist=False' in backref
    # http://docs.sqlalchemy.org/en/rel_0_8/orm/relationships.html#one-to-one
    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref(
            'profile', uselist=False, order_by=id) )

    # cloud coin, pay for resource
    coins = Column( Integer, default=0 )

    # resource
    cpu_used      = Column( Integer, default=0 )
    memory_used   = Column( Integer, default=0 )
    storage_used  = Column( Integer, default=0 )
    instance_used = Column( Integer, default=0 )

    cpu_total      = Column( Integer, default=0 )
    memory_total   = Column( Integer, default=0 )
    storage_total  = Column( Integer, default=0 )
    instance_total = Column( Integer, default=0 )

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

    # Other configure
    config = Column( Text() )


    def __init__(self, user):
        self.user_id = user.id

    def __repr__(self):
        return "UserProfile <%s>" % self.id

    @property
    def cpu_remain(self):
        return self.cpu_total - self.cpu_used

    @property
    def memory_remain(self):
        return self.memory_total - self.memory_used

    @property
    def instance_remain(self):
        return self.instance_total - self.instance_used

    @property
    def storage_remain(self):
        return self.storage_total - self.storage_used

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
            
    def update_resource_total(self):

        cpu_total = 0
        memory_total = 0
        instance_total = 0
        storage_total = 0

        now = datetime.datetime.now()

        for R in self.user.resources:
            if R.effect_date < now < R.expired_date:
                if R.type == R.T_CPU:
                    cpu_total += R.size
                elif R.type == R.T_MEMORY:
                    memory_total += R.size
                elif R.type == R.T_STORAGE:
                    storage_total += R.size
                elif R.type == R.T_INSTANCE:
                    instance_total += R.size

        self.cpu_total = cpu_total
        self.memory_total = memory_total
        self.storage_total = storage_total
        self.instance_total = instance_total


    def update_resource_used(self):

        cpu_used = 0
        memory_used = 0
        instance_used = 0
        storage_used = 0

        for I in self.user.instances:

            if I.is_running:
                cpu_used += I.cpus
                memory_used += I.memory

            instance_used += 1

            for S in I.storages:
                storage_used += S.size

        self.cpu_used = cpu_used
        self.memory_used = memory_used
        self.instance_used = instance_used
        self.storage_used = storage_used


    def update_resource(self):
        self.update_resource_total()
        self.update_resource_used()



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
