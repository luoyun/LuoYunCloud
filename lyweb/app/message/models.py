from datetime import datetime
from lyorm import ORMBase
from app.account.models import User

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text

from sqlalchemy.orm import backref,relationship

class Message(ORMBase):

    __tablename__ = 'message'

    id = Column( Integer, Sequence('message_id_seq'), primary_key=True ) 

    sender_id = Column( ForeignKey('auth_user.id') )
    sender = relationship("User", primaryjoin="User.id == Message.sender_id" )
    receiver_id = Column( ForeignKey('auth_user.id') )
    receiver = relationship("User",primaryjoin="User.id == Message.receiver_id" )

    subject = Column( Text )
    content = Column ( Text )

    created = Column(DateTime(), default=datetime.utcnow() )

    def __init__(self, sender, receiver, subject='', content=''):
        self.sender_id = sender.id
        self.receiver_id = receiver.id
        self.subject = subject
        self.content = content

    def __repr__(self):
        return _("[Message(%s:%s)]") % (self.id, self.subject)

