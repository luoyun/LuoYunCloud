import datetime

from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from ..language.models import Language

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])


entry_type = [
    (1, 'URL'),
]


class SiteNav(ORMBase):

    ''' Site navigation system '''

    __tablename__ = 'site_nav'

    id          = Column(Integer, Sequence('site_nav_id_seq'), primary_key=True)
    type        = Column(Integer)
    position    = Column(Integer, default=0)

    language_id = Column( ForeignKey('language.id') )
    language    = relationship("Language", backref=backref('site_navs', order_by=id))

    name        = Column(String(64))
    url         = Column(String(256), default='')
    target      = Column(String(1024))
    summary     = Column(String(256), default='')
    isnewopen   = Column(Boolean, default = False)

    created = Column(DateTime(), default=datetime.datetime.now)
    updated = Column(DateTime(), default=datetime.datetime.now)

    def __str__(self):
        return 'Site Nav <%s>' % self.id

    @property
    def type_str(self):
        for k, v in entry_type:
            if k == self.type:
                return v

        return _('Unknown')


class SiteEntry(ORMBase):

    ''' Site entry system '''

    __tablename__ = 'site_entry'

    id   = Column(Integer, Sequence('site_entry_id_seq'), primary_key=True)
    slug = Column(String(256))

    created = Column(DateTime(), default=datetime.datetime.now)
    updated = Column(DateTime(), default=datetime.datetime.now)

    def __str__(self):
        return 'SiteArticle <%s>' % self.id


class SiteArticle(ORMBase):

    __tablename__ = 'site_article'

    id = Column(Integer, Sequence('site_article_id_seq'), primary_key=True)

    language_id = Column( ForeignKey('language.id') )
    language    = relationship("Language")

    entry_id = Column( ForeignKey('site_entry.id') )
    entry    = relationship('SiteEntry', backref=backref('articles'))

    name    = Column(String(256))
    summary = Column(String(256))
    body    = Column(Text)

    # is_visible : can visible
    is_visible = Column(Boolean, default = True)

    created = Column(DateTime(), default=datetime.datetime.now)
    updated = Column(DateTime(), default=datetime.datetime.now)

    def __str__(self):
        return 'SiteArticle <%s>' % self.id

    @property
    def body_html(self):
        return YMK.convert( self.body )
