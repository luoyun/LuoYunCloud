from tornado.web import url
import app.message.views as msg

handlers = [

    url(r'/message/index', msg.Index, name='message:index'),
    url(r'/message/inbox', msg.Inbox, name='message:inbox'),
    url(r'/message/outbox', msg.Outbox, name='message:outbox'),
    url(r'/message/new', msg.NewMessage, name='message:new'),
    url(r'/message/([0-9]+)', msg.View, name='message:view'),
    url(r'/message/([0-9]+)/delete', msg.Delete, name='message:delete'),
    url(r'/message/([0-9]+)/reply', msg.Reply, name='message:reply'),
]

