from datetime import datetime
from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from ytime import htime, ftime

from app.auth.models import User
from yweb.orm import db

class LuoYunConfig(ORMBase):

    ''' This is a config style against unix

    Use DB, not text file.
    '''

    __tablename__ = 'configure'

    id = Column(Integer, Sequence('auth_session_id_seq'), primary_key=True)
    key  = Column( String(40) )
    value = Column( Text() )
    description  = Column( Text() )


    def __init__(self, key, value):
        self.key = key
        self.value = value


    def __repr__(self):
        return "[LuoYun(%s=%s)]" % (self.key, self.value)



class LyTrace(ORMBase):

    __tablename__ = 'lytrace'

    id = Column( Integer, Sequence('lytrace_id_seq'), primary_key=True )

    who_id = Column( ForeignKey('auth_user.id') )
    who = relationship("User", backref=backref('traces', order_by=id))

    when = Column( DateTime, default=datetime.now )
    comefrom = Column( String(512) ) # ip
    agent = Column( String(1024) )   # browser
    visit = Column( String(1024) )

    target_type = Column( Integer )
    target_id = Column( Integer )

    do = Column( String(1024) )
    isok = Column( Boolean, default = False) # result status
    result = Column( String(1024) )

    def __init__(self, who, comefrom, agent, visit):
        self.who_id = who.id
        self.comefrom = comefrom
        self.agent = agent
        self.visit = visit

    def __unicode__(self):
        return '%s: %s come from %s do "%s" , %s' % (
            ftime(self.when), self.who.username, self.comefrom,
            self.do, self.isok)

    @property
    def whois(self):
        if (self.who_id and db.query(User).get(self.who_id)):
            return self.who.username
