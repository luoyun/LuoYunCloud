#/usr/bin/env python2.5

import os, random, json, datetime
from hashlib import sha1

from yweb.orm import db, ORMBase
from app.language.models import Language

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

import settings


user_groups = Table('user_groups', ORMBase.metadata,
    Column('id', Integer, Sequence('user_groups_id_seq'), primary_key=True),
    Column('user_id', Integer, ForeignKey('auth_user.id')),
    Column('group_id', Integer, ForeignKey('auth_group.id'))
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


class User(ORMBase):

    __tablename__ = 'auth_user'

    id = Column(Integer, Sequence('auth_user_id_seq'), primary_key=True)
    username   = Column( String(30) )
    password   = Column( String(142) )
    email      = Column( String(64) )

    first_name = Column( String(30) )
    last_name  = Column( String(30) )
    nickname   = Column( String(30) )
    gender     = Column( Boolean )

    email_valid  = Column( Boolean, default = False )
    is_staff     = Column( Boolean, default = False )
    is_active    = Column( Boolean, default = True )
    is_superuser = Column( Boolean, default = False )
    is_locked    = Column( Boolean, default = False )

    notice       = Column( Integer, default=0 )

    # I think so.
    # TODO: 14 is en_US in language table
    language_id = Column( ForeignKey('language.id'), default=14 )
    language    = relationship("Language", backref=backref('users', order_by=id))

    last_active = Column( DateTime() )
    last_login  = Column( DateTime() )
    date_joined = Column( DateTime(), default=datetime.datetime.now )

    groups = relationship( 'Group', secondary=user_groups, backref='users' )

    def __init__(self, username, password, language=None):
        self.username = username
        self.nickname = username
        self.password = password
        if language:
            self.language_id = language.id

    def __unicode__(self):
        return '<user(%s)>' % self.username

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save()
        return check_password(raw_password, self.password, setter)

    @property
    def locale(self):
        return self.language.codename if self.language else 'en_US'

    @property
    def homedir(self):
        return os.path.join(settings.STATIC_PATH, 'user/%s' % self.id)

    @property
    def avatar_url(self):

        if os.path.exists(self.avatar_path):
            rp = 'user/%s/%s' % (self.id, settings.USER_AVATAR_NAME)
            return os.path.join(settings.STATIC_URL, rp)
        else:
            return settings.USER_AVATAR_DEFAULT

    @property
    def avatar_path(self):
        return os.path.join(self.homedir, 'thum_' + settings.USER_AVATAR_NAME)

    @property
    def avatar_mini(self):

        if os.path.exists(self.avatar_mini_path):
            return '<img src="/static/user/%s/%s" />' % (self.id, settings.USER_AVATAR_MINI_NAME)
        else:
            return '<i class="icon-user"></i>'

    @property
    def avatar_mini_path(self):
        return os.path.join(self.homedir, settings.USER_AVATAR_MINI_NAME)


    @property
    def avatar_orig_path(self):
        return os.path.join(self.homedir, settings.USER_AVATAR_NAME)

    def notify(self, notice=1):
        if self.notice and isinstance(self.notice, int):
            self.notice += notice
        else:
            self.notice = notice

        if self.notice < 0:
            self.notice = 0


    def init_account(self, db):
        if hasattr(settings, 'init_account'):
            callback = getattr(settings, 'init_account')
            callback(self, db)


class Permission(ORMBase):

    __tablename__ = 'auth_permission'

    id = Column(Integer, primary_key=True)
    name = Column( String(80) )
    codename = Column( String(100) )

    groups = relationship( "Group", secondary=group_permissions,
                           backref="permissions" )


    def __init__(self, name, codename):
        self.name = name
        self.codename = codename

    def __repr__(self):
        return _("Permission <%s>") % self.name



OpenID_TYPE = (
    (1, 'QQ'),
    )

class OpenID(ORMBase):

    __tablename__ = 'auth_openid'

    id = Column( Integer, Sequence('auth_openid_id_seq'), primary_key=True )

    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref( 'openid', order_by=id) )

    openid = Column( String(256) )
    type = Column( Integer )

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )

    # Other configure
    config = Column( Text() )


    def __init__(self, openid, _type):
        self.openid = openid
        self.type = _type

    def __str__(self):

        return 'OpenID <%s>' % self.id




class AuthKey(ORMBase):

    ''' a temp key for auth '''

    __tablename__ = 'auth_key'

    id = Column(Integer, Sequence('auth_key_id_seq'), primary_key=True)
    auth_key = Column( String(256) )
    auth_data = Column( String(1024) )
    expire_date  = Column( DateTime() )


    def __init__(self, data, seconds = 3600 * 24):
        self.auth_key = sha1(str(random.random())).hexdigest()
        self.auth_data = data
        self.expire_date = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
