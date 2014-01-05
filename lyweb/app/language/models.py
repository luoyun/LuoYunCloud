import datetime

from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref


class Language(ORMBase):

    ''' Language system '''

    __tablename__ = 'language'

    id       = Column(Integer, Sequence('language_id_seq'), primary_key=True)
    name     = Column(String(32))
    name_en  = Column(String(32))
    codename = Column(String(6))

    def __str__(self):
        return '<%s>' % self.codename


