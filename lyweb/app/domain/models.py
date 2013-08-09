import datetime
from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref


class UserDomain(ORMBase):

    __tablename__ = 'user_domain'

    id = Column( Integer, Sequence('user_domain_id_seq'), primary_key=True )
    domain = Column( String(256),  unique = True )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User", backref=backref('domains', order_by=id))

    instance_id = Column( ForeignKey('instance.id') )
    instance = relationship("Instance", backref=backref('domains', order_by=id))

    created = Column( DateTime, default=datetime.datetime.now )
    updated = Column( DateTime, default=datetime.datetime.now )


    def __init__(self, domain, user, instance):

        self.domain = domain
        self.user_id = user.id
        self.instance_id = instance.id

