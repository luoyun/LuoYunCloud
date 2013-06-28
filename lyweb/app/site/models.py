import datetime

from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text, \
    and_

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



class SiteConfig(ORMBase):

    ''' Global site config, k-v style'''

    __tablename__ = 'site_config'

    id = Column(Integer, Sequence('site_config_id_seq'), primary_key=True)
    key   = Column( String(256) )
    value = Column( Text )

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "SiteConfig <%s>" % self.id

    @classmethod
    def get(clc, db, key, default=None):
        x = db.query(clc).filter_by( key = key ).first()
        return x.value if x else default

    @classmethod
    def set(clc, db, key, value):

        x = db.query(clc).filter_by( key = key ).first()

        if x:
            x.value = value
        else:
            x = clc(key=key, value=value)

        db.add(x)
        db.commit()


class SiteLocaleConfig(ORMBase):

    ''' Global site locale config, select by locale language '''

    __tablename__ = 'site_locale_config'

    id = Column(Integer, Sequence('site_locale_config_id_seq'), primary_key=True)

    language_id = Column( ForeignKey('language.id') )
    language    = relationship("Language", backref=backref('site_locale_configs', order_by=id))

    key   = Column( String(256) )
    value = Column( Text() )

    def __repr__(self):
        return "SiteLocaleConfig <%s>" % self.id

    @classmethod
    def get(clc, db, key, language_id, default=None):

        x = db.query(clc).filter(
            and_(clc.key == key, clc.language_id == language_id )).first()
        return x.value if x else default


    @classmethod
    def set(clc, db, key, value, language_id):

        x = db.query(clc).filter(
            and_(clc.key == key, clc.language_id == language_id )).first()

        if x:
            x.value = value
        else:
            x = clc(key=key, value=value, language_id = language_id)

        db.add(x)
        db.commit()

    @property
    def html(self):
        return YMK.convert( self.value )



SITE_JOB_STATUS = (
    (1, _('Job is new') ),
    (2, _('Job is running') ),
    (3, _('Job is stoped') ),
    )
class SiteJob(ORMBase):

    __tablename__ = 'site_job'

    id = Column( Integer, Sequence('site_job_id_seq'), primary_key=True )

    # user is for permission
    user_id = Column( Integer, ForeignKey('auth_user.id', ondelete='CASCADE') )

    status = Column( Integer, default=1 )
    desc = Column( String(2048) )
    text = Column( Text )

    started = Column( DateTime() )
    updated = Column( DateTime() )
    created = Column( DateTime(), default=datetime.datetime.now )


    def __init__(self, user_id, desc ):
        self.user_id = user_id
        self.desc = desc

    def __repr__(self):
        return "SiteJob <%s>" % self.id

    def update_status(self, text):
        self.updated = datetime.datetime.now()
        self.text = text

    def set_started(self, text='started'):
        self.started = datetime.datetime.now()
        self.updated = datetime.datetime.now()
        self.text = text
        self.status = 2

    def set_ended(self, text='ended'):
        self.updated = datetime.datetime.now()
        self.text = text
        self.status = 3

    def is_stoped(self):
        return self.status == 3

    def is_running(self):
        return self.status == 2

