from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])


class WikiCatalog(ORMBase):

    __tablename__ = 'wiki_catalog'

    id = Column( Integer, Sequence('wiki_catalog_id_seq'), primary_key=True )

    name = Column( String(64) )
    summary = Column( String(1024) )
    description = Column( Text )

    position = Column( Integer , default = 0 )

    created = Column(DateTime(), default=datetime.utcnow())
    updated = Column(DateTime(), default=datetime.utcnow())


    def __init__(self, name, summary='', description=''):
        self.name = name
        self.summary = summary
        self.description = description

    def __repr__(self):
        return _("[WikiCatalog(%s)]") % self.name


class Topic(ORMBase):

    __tablename__ = 'topic'

    id = Column( Integer, Sequence('topic_id_seq'), primary_key=True )

    name = Column( String(512) )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship('User', backref=backref('topics',order_by=id) )

    catalog_id = Column( ForeignKey('wiki_catalog.id') )
    catalog = relationship('WikiCatalog', backref=backref('topics', order_by=id) )

    body = Column( Text )
    body_html = Column( Text )

    user_ip = Column( String(32) ) # TODO: delete, can record in another table
    views = Column( Integer, default = 0 )
    closed = Column( Boolean, default = False ) # TODO:

    created = Column(DateTime(), default=datetime.utcnow())
    updated = Column(DateTime(), default=datetime.utcnow())

    def __init__(self, catalog, user, name, body=''):

        self.catalog_id = catalog.id
        self.user_id = user.id
        self.name = name
        self.body = body
        self.body_html = YMK.convert( self.body )
        self.user_ip = '127.0.0.1'


    def __repr__(self):

        return _("[Topic(%s)]") % self.id

