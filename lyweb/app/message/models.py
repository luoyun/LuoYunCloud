from datetime import datetime
from lyorm import ORMBase
from app.account.models import User

from sqlalchemy import Column, Integer, BigInteger, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text

from sqlalchemy.orm import backref,relationship


class Message(ORMBase):

    __tablename__ = 'message'

    id = Column( BigInteger, Sequence('message_id_seq'), primary_key=True )

    reply_id = Column( ForeignKey('message.id') )

    sender_id = Column( ForeignKey('auth_user.id') )
    sender = relationship( "User", primaryjoin="User.id == Message.sender_id" )
    receiver_id = Column( ForeignKey('auth_user.id') )
    receiver = relationship( "User", primaryjoin="User.id == Message.receiver_id" )

    text_id = Column( ForeignKey('message_text.id') )
    text = relationship( "MessageText", primaryjoin="MessageText.id == Message.text_id" )

    isinbox = Column( Boolean, default = True ) # show in inbox ?
    isread = Column( Boolean, default = False )
    readtime = Column( DateTime ) # readtime and isread is repeated ?

    status = Column( Integer, default=1 ) # normal, delete, save ...


    def __init__(self, sender_id, receiver_id, text_id):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.text_id = text_id

    def __unicode__(self):
        return _("Message %s ( %s -> %s )") % (
            self.id, self.sender.username, self.receiver.username)



class MessageText(ORMBase):

    __tablename__ = 'message_text'

    id = Column( BigInteger, Sequence('message_text_id_seq'), primary_key=True ) 

    subject = Column( String(256) )
    body = Column( Text )

    sendtime = Column( DateTime, default=datetime.now )

    def __init__(self, subject, body):
        # TODO: safe html check
        self.subject = subject.replace('<', "&lt;").replace('>', "&gt;")
        self.body = body

    def __unicode__(self):
        return __("MessageText(%s)") % self.subject

