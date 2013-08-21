# coding: utf-8


import logging, datetime, time, re
import tornado
from lycustom import RequestHandler, has_permission
from tornado.web import authenticated, asynchronous

from app.auth.models import User
from app.message.models import Message, MessageText
from app.message.forms import MessageForm, NewMessageForm,ReplyMessageForm

from sqlalchemy.sql.expression import asc, desc

from yweb.utils.pagination import pagination

import re
reply_regex = re.compile(r'(\s*Re:\s*|\s*回复：\s*|\s*Re：\s*|\s*回复:\s*)', re.IGNORECASE)



class MessageRequestHandler(RequestHandler):

    def my_message(self, ID):
        M = self.db.query(Message).get( ID )

        if not M:
            self.write( self.trans(_('Can not find message %s')) % ID )
            return None

        UID = self.current_user.id
        if M.receiver_id == UID or M.sender_id == UID:
            return M


        self.write( self.trans(_("You have no permissions to read this message!")) )
        return None


    def my_box_list(self, show="inbox"):

        UID = self.current_user.id

        page_size = self.get_argument_int('sepa', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'DESC')

        if by == 'status':
            by = Message.status
        elif by == 'isread':
            by = Message.isread
        elif by == 'readtime':
            by = Message.readtime
        elif by == 'sender':
            by = Message.sender_id
        else:
            by = Message.id

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        if show == "inbox":
            ml = self.db.query(Message).filter_by(
                receiver_id=UID, isinbox=True)
        elif show == "outbox":
            ml = self.db.query(Message).filter_by(
                sender_id=UID, isinbox=False).filter(
                Message.receiver_id != None)
        elif show == "notice":
            ml = self.db.query(Message).filter(
                Message.receiver_id == None)
        else:
            return {}

        total = ml.count()

        ml = ml.order_by( by_exp ).slice(start, stop).all()

        page_html = pagination(self.request.uri, total, page_size, cur_page)

        return { 'MESSAGE_LIST': ml,
                 'PAGE_HTML': page_html,
                 'TOTAL': total,
                 'SORT': sort, 'BY': by }


class Index(MessageRequestHandler):

    @authenticated
    def get(self):
        self.render( 'message/index.html', title = self.trans(_('Message Home')) )


class Inbox(MessageRequestHandler):

    @authenticated
    def get(self):

        unread = self.db.query(Message.id).filter_by(
            receiver_id=self.current_user.id, isread=False).count()

        d = { 'title': self.trans(_('My inbox')), 'unread': unread }
        d.update( self.my_box_list() )

        self.render( 'message/inbox.html', **d )



class Outbox(MessageRequestHandler):

    @authenticated
    def get(self):

        d = { 'title': self.trans(_('My outbox')) }
        d.update( self.my_box_list(show="outbox") )

        self.render( 'message/outbox.html', **d )


class View(MessageRequestHandler):

    @authenticated
    def get(self, ID):

        M = self.my_message( ID )
        d = { 'title': self.trans(_('View message %s')) % ID, 'M': M,
              'ININBOX': None }
        if M:
            if M.receiver_id == self.current_user.id:
                # My outbox message
                d['ININBOX'] = "INBOX"

            if not M.isread:
                M.isread = True
                M.receiver.notify(-1)

            if not M.readtime:
                M.readtime = datetime.datetime.now()

            self.db.commit()

            if M.reply_id: # a hack to add reply obj
                M.reply = self.db.query(Message).get( M.reply_id )

        self.render('message/view_message.html', **d)



class Delete(MessageRequestHandler):

    @authenticated
    def get(self, id):

        M = self.my_message(id)
        if M:
            x = self.db.query(Message.id).filter_by(
                text_id = M.text_id).count()

            if not M.isread:
                M.receiver.notify(-1)

            quote_list = self.db.query(Message).filter_by(
                reply_id = M.id)
            for q in quote_list:
                if ( q.receiver_id == self.current_user.id or
                     q.sender_id == self.current_user.id ):
                    q.reply_id = None

            self.db.delete( M )

            if x == 1: # Delete text
                self.db.delete( M.text )

            self.db.commit()

            if not self.get_argument('ajax', None):
                self.redirect(self.reverse_url("message:inbox"))

        else:
            self.write( self.trans(_('This is not your message !')) )



class New(MessageRequestHandler):

    @authenticated
    def get(self):

        UID = self.get_argument('user', 0)
        ORIG_MSG_ID = self.get_argument('origmsg', 0)

        form = MessageForm(self)

        if UID:
            receiver = self.db.query(User).get( UID )
            if receiver:
                form.to.data = receiver.username
        else:
            receiver = None

        if ORIG_MSG_ID:
            M = self.db.query(Message).get( ORIG_MSG_ID )
            if M:
                form.to.data = M.sender.username
                subject = reply_regex.sub('', M.text.subject)
                form.subject.data = self.trans(_('Re: %s')) % subject
                form.text.data = '<pre>%s</pre>' % M.text.body


        d = { 'title': self.trans(_('Send message')),
              'form': form, 'RECEIVER': receiver }
        self.render( 'message/send_message.html', **d)


    @authenticated
    def post(self):

        receiver = None

        form = MessageForm(self)
        if form.validate():
            receiver = self.db.query(User).filter_by(username=form.to.data).first()
            if receiver:
                T = MessageText( subject = form.subject.data,
                                 body = form.text.data )
                self.db.add(T)
                self.db.commit()

                M = Message( sender_id = self.current_user.id,
                             receiver_id = receiver.id, text_id = T.id )

                self.db.add(M)

                # send a message to myself
                if receiver.id != self.current_user.id:
                    M = Message( sender_id = self.current_user.id,
                                 receiver_id = receiver.id, text_id = T.id )
                    M.isinbox = False
                    self.db.add(M)

                receiver.notify()
                self.db.commit()

                url = self.reverse_url('message:inbox')
                return self.redirect(url)

            else:
                form.to.errors.append( self.trans(_('Can not find user %s')) % form.to.data )
            # end if

        d = { 'title': self.trans(_('Send message')),
              'form': form, 'RECEIVER': receiver }

        self.render( 'message/send_message.html', **d )



class Reply(MessageRequestHandler):

    @authenticated
    def get(self, ID):

        M = self.my_message( ID )
        if M:
            d = { 'title': self.trans(_('Reply message %s')) % ID, 'M': M }
            self.render( 'message/reply_message.html', **d)

        else:
            self.render( self.trans(_('Can not find message %s')) % ID )


    @authenticated
    def post(self, ID):

        M = self.my_message( ID )
        if not M:
            return self.write( self.trans(_('Can not find message %s')) % ID )

        body = self.get_argument('text', '')
        if not body:
            return self.write( self.trans(_('No content write !')) )

        subject = reply_regex.sub('', M.text.subject)
        subject = self.trans(_('Re: %s')) % subject
        T = MessageText( subject = subject, body = body )
        self.db.add(T)
        self.db.commit()

        NewMsg = Message( sender_id = self.current_user.id,
                     receiver_id = M.sender_id, text_id = T.id )
        NewMsg.reply_id = M.id

        self.db.add(NewMsg)

        # do not send a message to myself
        if M.sender_id != self.current_user.id:
            NewMsg = Message( sender_id = self.current_user.id,
                              receiver_id = M.sender_id,
                              text_id = T.id )
            NewMsg.reply_id = M.id
            NewMsg.isinbox = False
            self.db.add(NewMsg)

        M.sender.notify()
        self.db.commit()

        url = self.reverse_url('message:outbox')
        self.redirect(url)


class SendNotice(MessageRequestHandler):
    ''' Send message to all user in site. '''

    @has_permission('admin')
    def get(self):

        form = MessageForm(self)

        d = { 'title': self.trans(_('Send a notice to all user')),
              'form': form }
        self.render( 'message/send_notice.html', **d)


    @has_permission('admin')
    def post(self):

        form = MessageForm(self)

        d = { 'title': self.trans(_('Send a notice to all user')),
              'form': form }

        if form.validate():
            to = form.to.data

            T = MessageText( subject = form.subject.data,
                             body = form.text.data )
            self.db.add(T)
            self.db.commit()

            current_user_id = self.current_user.id
            text_id = T.id

            M = Message( sender_id = current_user_id,
                         receiver_id = None, text_id = text_id )
            M.isinbox = False
            self.db.add(M)

            # TODO: select method
            for U in self.db.query(User):
                M = Message( sender_id = current_user_id,
                             receiver_id = U.id, text_id = text_id )
                self.db.add(M)
                U.notify()

            self.db.commit()

            url = self.reverse_url('message:notice')
            return self.redirect( url )

        # failed
        self.render( 'message/send_notice.html', **d)



class NoticeHome(MessageRequestHandler):
    ''' Get all site notice message '''

    @has_permission('admin')
    def get(self):

        MSG_ID = self.get_argument_int('message', 0)
        if MSG_ID:
            M = self.db.query(Message).get( MSG_ID )
            d = { 'title': self.trans(_('View notice %s')) % MSG_ID, 'M': M }
            self.render( 'message/notice_view.html', **d)

        else:
            d = { 'title': self.trans(_('Send a notice to all user')) }
            d.update( self.my_box_list(show="notice") )
            self.render( 'message/notice.html', **d)


class NoticeDelete(MessageRequestHandler):
    ''' Delete a notice '''

    @has_permission('admin')
    def get(self, ID):

        M = self.db.query(Message).get( ID )
        if M.receiver_id:
            self.write( self.trans(_('This is not a notice !')) )
        else:
            if not self.db.query(Message.id).filter_by(
                text_id = M.text_id).count():
                # Delete text
                self.db.delete( M.text )

            self.db.delete( M )
            self.db.commit()

            if not self.get_argument('ajax', None):
                self.redirect(self.reverse_url("message:notice"))

