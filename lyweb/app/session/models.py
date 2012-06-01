from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref



class Session(ORMBase):

    __tablename__ = 'auth_session'

    id = Column(Integer, Sequence('auth_session_id_seq'), primary_key=True)
    session_key  = Column( String(40) )
    session_data = Column( Text() )
    expire_date  = Column( DateTime() )

    def __init__(self, key, data):
        self.session_key = key
        self.session_data = data
        # TODO:
        now = datetime.utcnow()
        self.expire_date = datetime(now.year, now.month,
                                    now.day, now.hour)

    def __repr__(self):
        return _("[Session(%s)]") % self.session_key




