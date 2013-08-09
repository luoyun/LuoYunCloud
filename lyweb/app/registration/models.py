#/usr/bin/env python2.5

import os, random, json, datetime
from hashlib import sha1

from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref



class RegistrationApply(ORMBase):
    '''registration apply'''

    __tablename__ = 'registration_apply'

    id = Column(Integer, primary_key=True)
    email    = Column( String(32) )
    key      = Column( String(128) )
    created  = Column( DateTime(), default=datetime.datetime.now )

    def __init__(self, email):
        self.email = email
        self.key = sha1(str(random.random())).hexdigest()

    def __repr__(self):
        return 'RegistrationApply <%s>' % self.email
