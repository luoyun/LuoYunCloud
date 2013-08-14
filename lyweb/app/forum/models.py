#/usr/bin/env python2.5

import os, random, json, datetime
import Image
import tempfile
import logging
from hashlib import sha1

from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from yweb.utils.base import makesure_path_exist

import settings
from settings import runtime_data
from app.site.utils import get_site_config

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'codehilite', 'tables'])


forum_catalog__manager = Table('forum_catalog__manager', ORMBase.metadata,
    Column('id', Integer, Sequence('forum_catalog__manager_id_seq'), primary_key=True),
    Column('catalog_id', Integer, ForeignKey('forum_catalog.id')),
    Column('user_id', Integer, ForeignKey('auth_user.id'))
)

forum_catalog__allowed = Table('forum_catalog__allowed', ORMBase.metadata,
    Column('id', Integer, Sequence('forum_catalog__allowed_id_seq'), primary_key=True),
    Column('catalog_id', Integer, ForeignKey('forum_catalog.id')),
    Column('user_id', Integer, ForeignKey('auth_user.id'))
)

forum_topic__tag = Table('forum_topic__tag', ORMBase.metadata,
    Column('id', Integer, Sequence('forum_topic__tag_id_seq'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('forum_topic.id')),
    Column('tag_id', Integer, ForeignKey('forum_topic_tag.id'))
)


forum_topic__collector = Table(
    'forum_topic__collector', ORMBase.metadata,
    Column('id', Integer, Sequence('forum_topic__collector_id_seq'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('forum_topic.id')),
    Column('collector_id', Integer, ForeignKey('auth_user.id'))
)


class ForumForbiddenUser(ORMBase):
    __tablename__ = 'forum_forbidden_user'

    id = Column( Integer, Sequence('forum_forbidden_user_id_seq'), primary_key=True )

    user_id = Column(Integer, ForeignKey('auth_user.id'))
    operator_id = Column(Integer, ForeignKey('auth_user.id'))

    updated = Column(DateTime(), default=datetime.datetime.now)
    created = Column(DateTime(), default=datetime.datetime.now)



class ForumCatalog(ORMBase):
    '''Forum Catalog'''

    __tablename__ = 'forum_catalog'

    id        = Column(Integer, Sequence('forum_catalog_id_seq'), primary_key=True)
    parent_id = Column(Integer, ForeignKey('forum_catalog.id'))
    children  = relationship("ForumCatalog", order_by = id)

    name        = Column(String(128))
    summary     = Column(String(256))
    description = Column(Text)

    position = Column( Integer, default = 0 )

    # is_private : just allowed_users can talk
    is_private = Column(Boolean, default = False)
    is_visible = Column(Boolean, default = True)

    managers = relationship('User', secondary=forum_catalog__manager)
    allowed_users = relationship('User', secondary=forum_catalog__allowed)

    language_id = Column( ForeignKey('language.id') )
    language    = relationship("Language", order_by=id)

    updated = Column(DateTime(), default=datetime.datetime.now)
    created = Column(DateTime(), default=datetime.datetime.now)


    def __init__(self, name, summary=None, description=None):
        self.name        = name
        self.summary     = summary
        self.description = description


    def __str__(self):
        return 'Catalog (%s)' % self.name


    @property
    def logourl(self):

        dataurl = runtime_data.get('site.data.url')
        if not dataurl:
            dataurl = get_site_config( 'site.data.url', '/dl/' )
            runtime_data['site.data.url'] = dataurl

        thumb_file = os.path.join( self.logodir, 'thumb.png')

        if os.path.exists( thumb_file ):
            return '%s/forum/catalog/%s/thumb.png' % (
                dataurl.rstrip('/'), self.id )
        else:
            return '/static/image/forum/catalog_logo.png'


    @property
    def logodir(self):

        datapath = runtime_data.get('site.data.path')
        if not datapath:
            datapath = get_site_config(
                'site.data.path', '/opt/LuoYun/data/' )
            runtime_data['site.data.path'] = datapath

        return os.path.join(datapath, 'forum/catalog/%s' % self.id)


    def save_logo(self, request_files):
        ''' save logo file
        request_files = self.request.files['logo']
        '''

        logodir = self.logodir

        if not makesure_path_exist( logodir ):
            return _('Create logodir "%s" failed') % logodir

        max_size = settings.APPLIANCE_LOGO_MAXSIZE

        for f in request_files:

            if len(f['body']) > max_size:
                return _('Logo must smaller than %s !') % human_size(max_size)

            save_raw_file = os.path.join(logodir, 'r.png')
            save_raw_file = os.path.join(logodir, 'thumb.png')

            tf = tempfile.NamedTemporaryFile()
            tf.write(f['body'])
            tf.seek(0)

            try:
                img = Image.open(tf.name)

                # can convert image type
                img.save( save_raw_file )

                img.thumbnail((120, 120), Image.ANTIALIAS)
                img.save( save_thumb_file )

            except Exception, emsg:
                e = _('Save %(filename)s failed: %(emsg)s') % {
                    'filename': f.get('filename'), 'emsg': emsg }
                logging.error( e )
                return e

            tf.close()



TOPIC_STATUS = (
    (0, _('Normal')),
    (1, _('Deleted')),
)
MARKUP_LANGUAGE = (
    (1, _('markdown')),
    (2, _('WYSIWYM')),
    )
class ForumTopic(ORMBase):
    '''Forum Topic'''

    __tablename__ = 'forum_topic'

    id         = Column(Integer, Sequence('forum_topic_id_seq'), primary_key=True)
    catalog_id = Column(Integer, ForeignKey('forum_catalog.id'))
    catalog    = relationship('ForumCatalog', order_by = id)

    name    = Column(String(256))
    summary = Column(String(2048))
    body    = Column(Text)

    user_id = Column(Integer, ForeignKey('auth_user.id'))
    user = relationship('User', order_by = id)

    # is_locked : can not edit by anyone except admin
    is_locked  = Column(Boolean, default = False)
    # is_closed : can not reply now
    is_closed  = Column(Boolean, default = False)
    # is_visible : can visible
    is_visible = Column(Boolean, default = True)
    is_top = Column(Boolean, default = False)

    like   = Column(Integer, default=0)
    unlike = Column(Integer, default=0)
    visit  = Column(Integer, default=0) # view times

    position = Column( Integer, default = 0 )

    status = Column(Integer, default=0) # topic status

    tags = relationship('ForumTopicTag', secondary=forum_topic__tag,
                        backref='topics' )

    collectors = relationship(
        'User', secondary=forum_topic__collector, backref='topics' )

    #TODO: like/unlike log

    markup_language =  Column(Integer, default=1)

    updated = Column(DateTime(), default=datetime.datetime.now)
    created = Column(DateTime(), default=datetime.datetime.now)


    def __init__(self, name, summary, body, catalog=None):
        self.name = name
        self.summary = summary
        self.body = body
        if catalog:
            self.catalog_id = catalog.id

    def __str__(self):
        return 'Topic %s' % self.id

    @property
    def body_html(self):
        if self.markup_language == 1: # Markdown
            return YMK.convert( self.body )
        else:
            return self.body

    def set_status(self, status):
        if status == 'deleted':
            self.status = 1

    @property
    def is_deleted(self):
        return self.status == 1

    @property
    def language(self):
        if self.markup_language == 1:
            return 'markdown'

        else:
            return None
            

class ForumTopicTag(ORMBase):
    '''Forum Topic Tag'''

    __tablename__ = 'forum_topic_tag'

    id = Column(Integer, Sequence('forum_topic_tag_id_seq'), primary_key=True)
    name = Column(String(32))
    description = Column(Text)
    hit = Column(Integer, default=1)

    updated = Column(DateTime(), default=datetime.datetime.now)
    created = Column(DateTime(), default=datetime.datetime.now)

    def __init__(self, name):
        self.name        = name

    def __str__(self):
        return 'Tag (%s)' % self.name


class ForumPost(ORMBase):

    __tablename__ = 'forum_post'

    id       = Column(Integer, Sequence('forum_post_id_seq'), primary_key=True)
    topic_id = Column(Integer, ForeignKey('forum_topic.id'))
    topic = relationship('ForumTopic', backref='posts', order_by = id)

    # parent post
    parent_id  = Column(Integer, ForeignKey('forum_post.id'))

    body = Column(Text)
    markup_language = Column(Integer, default=1)

    user_id = Column(Integer, ForeignKey('auth_user.id'))
    user = relationship('User', order_by = id)

    # is_locked : can not edit by anyone except admin
    is_locked  = Column(Boolean, default = False)
    # is_visible : can visible
    is_visible = Column(Boolean, default = True)

    like   = Column(Integer, default=0)
    unlike = Column(Integer, default=0)

    updated = Column(DateTime(), default=datetime.datetime.now)
    created = Column(DateTime(), default=datetime.datetime.now)


    def __init__(self, topic, body):
        self.body = body
        if topic:
            self.topic_id = topic.id

    def __str__(self):
        return '<Post (%s)>' % self.id

    @property
    def body_html(self):
        if self.markup_language == 1: # Markdown
            return YMK.convert( self.body )
        else:
            return self.body



class ForumTopicVote(ORMBase):

    __tablename__ = 'forum_topic_vote'

    id = Column(Integer, Sequence('forum_topic_vote_id_seq'), primary_key=True)
    
    topic_id = Column(Integer, ForeignKey('forum_topic.id'))
    topic = relationship('ForumTopic', backref='votes', order_by = id)

    user_id = Column(Integer, ForeignKey('auth_user.id'))
    user = relationship('User', order_by = id)

    value = Column(Integer)

    created = Column(DateTime(), default=datetime.datetime.now)


class ForumPostVote(ORMBase):

    __tablename__ = 'forum_post_vote'

    id = Column(Integer, Sequence('forum_post_vote_id_seq'), primary_key=True)
    
    post_id = Column(Integer, ForeignKey('forum_post.id'))
    post = relationship('ForumPost', backref='votes', order_by = id)

    user_id = Column(Integer, ForeignKey('auth_user.id'))
    user = relationship('User', order_by = id)

    value = Column(Integer)

    created = Column(DateTime(), default=datetime.datetime.now)

