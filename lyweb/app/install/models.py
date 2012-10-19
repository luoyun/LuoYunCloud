from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref



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
        return _("[LuoYun(%s=%s)]") % (self.key, self.value)




