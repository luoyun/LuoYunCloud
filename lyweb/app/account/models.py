#/usr/bin/env python2.5
#Noah Gift

import os, random
from hashlib import sha1

from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

import settings



user_groups = Table('user_groups', ORMBase.metadata,
    Column('id', Integer, Sequence('user_groups_id_seq'), primary_key=True),
    Column('user_id', Integer, ForeignKey('auth_user.id')),
    Column('group_id', Integer, ForeignKey('auth_group.id'))
)

user_permissions = Table('user_permissions', ORMBase.metadata,
    Column('id', Integer, Sequence('user_permissions_id_seq'), primary_key=True),
    Column('user_id', Integer, ForeignKey('auth_user.id')),
    Column('permission_id', Integer, ForeignKey('auth_permission.id')),
)


group_permissions = Table('group_permissions', ORMBase.metadata,
    Column('id', Integer, Sequence('group_permissions_id_seq'), primary_key=True),
    Column('group_id', Integer, ForeignKey('auth_group.id')),
    Column('permission_id', Integer, ForeignKey('auth_permission.id')),
)


class Group(ORMBase):

    __tablename__ = 'auth_group'

    id = Column(Integer, Sequence('auth_group_id_seq'), primary_key=True)
    name = Column( String(30) )
    description = Column( Text() )

    #TODO: a flag, can not delete when the flag is set !!!
    islocked = Column( Boolean, default = False)


    def __init__(self, name, description = None, islocked = False):
        self.name = name
        self.islocked = islocked
        if description:
            self.description = description


    def __repr__(self):
        return _("[Group(%s)]") % self.name


    @property
    def avatar_url(self):

        avatar = os.path.join( settings.STATIC_PATH,
                               'group/%s/avatar' % self.id )
        if os.path.exists(avatar):
            return '%sgroup/%s/avatar' % (settings.STATIC_URL, self.id)

        return os.path.join(settings.THEME_URL, 'img/user-group-icon.png')



class User(ORMBase):

    __tablename__ = 'auth_user'

    id = Column(Integer, Sequence('auth_user_id_seq'), primary_key=True)
    username = Column(String(30))
    password = Column(String(142))

    # TODO: if user is locked, could not login again.
    islocked = Column( Boolean, default = False )

    last_login = Column(DateTime(), default=datetime.utcnow())
    date_joined = Column(DateTime(), default=datetime.utcnow())

    groups = relationship( "Group", secondary=user_groups,
                           backref="users" )

    permissions = relationship( "Permission", secondary=user_permissions,
                           backref="users" )

    profile = relationship("UserProfile", uselist=False, backref="user")
    #TODO: a flag, can not delete when the flag is set !!!

    last_active = Column( DateTime() )
    last_entry = Column( String(256) )


    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return _("[User(%s)]") % self.username


    # TODO
    def notify(self):
        ''' Add a notification to user '''

        self.profile.notification += 1
        

    def decrease_notification(self):

        # TODO: to avoid a negative number !
        if self.profile.notification > 0:
            self.profile.notification -= 1

    @property
    def avatar_url(self):

        avatar = os.path.join( settings.STATIC_PATH,
                               'user/%s/avatar' % self.id )
        if os.path.exists(avatar):
            return '%suser/%s/avatar' % (settings.STATIC_URL, self.id)

        return os.path.join(settings.THEME_URL, 'img/user.png')

        

class UserProfile(ORMBase):

    __tablename__ = 'user_profile'

    id = Column( Integer, Sequence('user_profile_id_seq'), primary_key=True )

    user_id = Column( Integer, ForeignKey('auth_user.id') )
    first_name = Column( String(32) )
    last_name = Column( String(32) )
    gender = Column( Boolean )

    locale = Column( String(16), default='zh_CN' ) # TODO: select list
    email = Column( String(64) )

    # All notification of LuoYun System
    notification = Column( Integer, default=0 )

    # resource limit
    memory = Column( Integer, default=256 )  # 256 M
    cpus = Column( Integer, default=1 )      # 1 core
    instances = Column( Integer, default=3 ) # 3 instances
    storage = Column( Integer, default=2 )   # 2 G


    def __init__(self, user, email=''):
        self.user_id = user.id
        self.email = email

        if hasattr(settings, 'USER_DEFAULT_MEMORY'):
            self.memory = settings.USER_DEFAULT_MEMORY
        if hasattr(settings, 'USER_DEFAULT_CPUS'):
            self.cpus = settings.USER_DEFAULT_CPUS
        if hasattr(settings, 'USER_DEFAULT_INSTANCES'):
            self.instances = settings.USER_DEFAULT_INSTANCES
        if hasattr(settings, 'USER_DEFAULT_STORAGE'):
            self.instances = settings.USER_DEFAULT_STORAGE

    def __repr__(self):
        return _("[UserProfile(%s)]") % (self.user_id)



class Permission(ORMBase):

    __tablename__ = 'auth_permission'

    id = Column(Integer, Sequence('auth_permission_id_seq'), primary_key=True)
    name = Column( String(80) )
    codename = Column( String(100) )

    groups = relationship( "Group", secondary=group_permissions,
                           backref="permissions" )


    def __init__(self, name, codename):
        self.name = name
        self.codename = codename

    def __repr__(self):
        return _("[UserPermission(%s)]") % self.name




class ApplyUser(ORMBase):

    ''' Apply a registration on LuoYun '''

    __tablename__ = 'apply_user'

    id = Column(Integer, Sequence('apply_user_id_seq'), primary_key=True)
    email    = Column( String(32) )
    key      = Column( String(128) )
    ip       = Column( String(32) )
    created  = Column( DateTime(), default=datetime.utcnow() )

    def __init__(self, email, ip):
        self.email = email
        self.ip = ip
        self.key = sha1(str(random.random())).hexdigest()


    def __repr__(self):
        return _("[ApplyUser(%s)]") % self.username



class UserResetpass(ORMBase):

    ''' reset password apply '''

    __tablename__ = 'user_resetpass'

    id = Column(Integer, Sequence('user_resetpass_id_seq'), primary_key=True)

    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User", order_by = id)

    key = Column( String(128) )

    created  = Column( DateTime(), default=datetime.utcnow() )
    completed  = Column( DateTime() )


    def __init__(self, user):
        self.key = sha1(str(random.random())).hexdigest()
        self.user = user
        self.user_id = user.id


    def __repr__(self):
        return _("[User reset password apply (%s)]") % self.id

