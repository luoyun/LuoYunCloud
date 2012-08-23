# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import LyRequestHandler,fulltime
from tornado.web import authenticated, asynchronous

from app.account.models import User
from app.message.models import Message
from app.message.forms import NewMessageForm,ReplyMessageForm


class MessageRequestHandler(LyRequestHandler):

    def get_message(self, id):
        message = self.db2.query(Message).get(id)

        if not message:
            self.write( _('Have not found message %s') % id )
            return None

        if not ( message.receiver_id == self.current_user.id or
                 message.sender_id == self.current_user.id ) :
            self.write( _("You have no permissions to read this message!") )
            return None

        return message


class Index(MessageRequestHandler):

    @authenticated
    def get(self):
        self.render( 'message/index.html', title = _('Message Home') )


class Inbox(MessageRequestHandler):

    @authenticated
    def get(self):

        messages = self.db2.query(Message).filter_by( receiver_id=self.current_user.id ).order_by(Message.created.desc()).all()
        unread = self.db2.query(Message).filter_by( receiver_id=self.current_user.id, read=False ).all()

        d = {
            'title': _('Message Inbox'),
            'messages': messages,
            'user': self.current_user,
            'unread': len(unread)
        }
        self.render( 'message/inbox.html', **d )


class Outbox(MessageRequestHandler):

    @authenticated
    def get(self):

        messages = self.db2.query(Message).filter_by(sender_id=self.current_user.id ).order_by(Message.created.desc()).all()
        self.render( 'message/outbox.html', title = _('Message Outbox'), messages=messages, user = self.current_user )


class View(MessageRequestHandler):

    @authenticated
    def get(self, id):

        message = self.get_message(id)
        if not message: return

        d = { 'title': _('View Message: %s') % message.subject,
              'message': message, 'user': self.current_user }

        if not message.read:
            message.read = True
            message.receiver.decrease_notification()
            self.db2.commit()
        
        self.render('message/view_message.html', **d)


class NewMessage(MessageRequestHandler):

    @authenticated
    def get(self):

        id = self.get_argument('userid', -1)
        sendto = self.db2.query(User).get(id)
        form = NewMessageForm()
        if sendto:
            form = NewMessageForm(sendto = sendto.username)

        self.render( 'message/new_message.html', title = _('New Message'), form = form )

    @authenticated
    def post(self):

        form = NewMessageForm( self.request.arguments )
        if form.validate():
            # convert username to user id
            you = self.db2.query(User).filter_by(username=form.sendto.data).first()
            if you:
                m = Message( sender = self.current_user,
                             receiver = you,
                             subject = form.subject.data,
                             content = form.content.data)

                self.db2.add(m)
                self.db2.commit()

                m.receiver.notify()
                self.db2.commit()

                url = self.reverse_url('message:outbox')
                return self.redirect(url)
            else:
                form.sendto.errors.append( _('No such user !') ) 
            # end if

        self.render( 'message/new_message.html', title = _('New Message'), form = form )


class Delete(MessageRequestHandler):

    @authenticated
    def get(self, id):

        message = self.get_message(id)
        if not message: return

        if not message.read:
            message.receiver.decrease_notification()

        self.db2.delete(message)
        self.db2.commit()
        self.write('Delete message %s success !' % id)
        return self.redirect(self.reverse_url("message:outbox"))


class Reply(MessageRequestHandler):

    @authenticated
    def get(self, id):

        message = self.get_message(id)
        if not message: return

        # compose repily message content
        reply = "\n".join(map(lambda line:"> "+line, message.content.split("\n")))

        content = "On %s, %s wrote:\n%s" %(fulltime(message.created), message.sender.username, reply)
        form = ReplyMessageForm(subject="Re:"+message.subject, content=content)
        self.render( 'message/reply_message.html', tilte = _('Reply Message'), message = message, form = form)

    @authenticated
    def post(self, id):

        message = self.db2.query(Message).get(id)
        if not message:
            return self.write('Have not found message %s' % id)

        form = ReplyMessageForm( self.request.arguments )
        if form.validate():
            m = Message( sender = message.receiver, 
                         receiver = message.sender, 
                         subject = form.subject.data,
                         content = form.content.data)

            self.db2.add(m)
            self.db2.commit()

            m.receiver.notify()
            self.db2.commit()

            url = self.reverse_url('message:outbox')
            return self.redirect(url)

        self.render( 'message/reply_message.html', tilte = _('Reply Message'), message = message, form = form)
