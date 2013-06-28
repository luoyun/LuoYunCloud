#! /usr/bin/env python

import sys
import os
import signal
import threading

## Global PATH
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../lib'))
sys.path.insert(0, '/opt/LuoYun/web/')

# TODO: i18n is too ugly yet
import __builtin__
__builtin__.__dict__['_'] = lambda s: s


import logging
from threading import Thread

from app.auth.models import User
from app.site.models import SiteJob, SiteConfig
from yweb import orm

dbsession = orm.create_session()
db = dbsession()

from yweb.quemail import QueMail, Email

def init_quemail():

    qm = QueMail.get_instance()

    smtp_server = SiteConfig.get(
        db, 'notice.smtp.server', '127.0.0.1')
    smtp_port = int(SiteConfig.get(
            db, 'notice.smtp.port', 25 ))
    smtp_username = SiteConfig.get(
        db, 'notice.smtp.username', None)
    smtp_password = SiteConfig.get(
        db, 'notice.smtp.password', None)

    print 'smtp_server   = ', smtp_server
    print 'smtp_port     = ', smtp_port
    print 'smtp_username = ', smtp_username
    print 'smtp_password = ', smtp_password

    qm.init( smtp_server, smtp_username, smtp_password,
             smtp_port = smtp_port )

    qm.start()


def mailto_address( data ):

    to = data.get('to', None)
    to_user_id = data.get('to_user_id', None)
    subject = data.get('subject', None)
    body = data.get('body', None)
    adr_from = SiteConfig.get(
        db, 'notice.smtp.fromaddr', 'admin@localhost')

    if not (to or to_user_id):
        logging.error( _('mailto_address: no address find') )
        return

    qm = QueMail.get_instance()

    if to:
        username = to.split('@')[0]

    if to_user_id:
        U = db.query(User).get( to_user_id )
        if U:
            username = U.nickname if U.nickname else U.username
            to = U.email

    d = { 'subject': subject, 'BODY_HTML': body,
          'username': username }

    body = render_template('custom/mail_template.html', **d)

    if body:
        e = Email( subject = subject, text = body,
                   adr_to = to,
                   adr_from = adr_from, mime_type = 'html' )
        qm.send( e )

    else:
        logging.error( _('render email body for html failed.') )


def mailto_user_list( data ):

#    logging.debug('send mail to %s' % data)

    UID_LIST = data.get('ID_LIST', [])
    uid = data.get('uid', None)
    subject = data.get('subject', None)
    body = data.get('body', None)
    adr_from = SiteConfig.get(
        db, 'notice.smtp.fromaddr', 'admin@localhost')

    job = SiteJob( uid, _('send mail to user list.') )
    job.set_started()
    db.add( job )
    db.commit()

    # send mail
    qm = QueMail.get_instance()

    if UID_LIST:
        USER_LIST = []
        for ID in UID_LIST:
            U = db.query(User).get( ID )
            if U:
                USER_LIST.append( U )
    else:
        USER_LIST = db.query(User)

    for U in USER_LIST:

        text = _('send mail to %s: %s (%s)') % (U.id, U.username, U.email)

        logging.debug( text )

        job.update_status( text )
        db.commit()

        time.sleep(1)

        if not (U and U.email and U.email_valid):
            continue

        d = { 'subject': subject, 'BODY_HTML': body,
              'username': U.nickname if U.nickname else U.username }
        body = render_template('custom/mail_template.html', **d)

        if body:

            e = Email( subject = subject, text = body,
                       adr_to = U.email,
                       adr_from = adr_from, mime_type = 'html' )

#            qm.send( e )

        else:
            logging.error( _('render email body for html failed.') )

    job.set_ended()
    db.commit()


def exit_handler(_signal, frame):

    if _signal == signal.SIGINT:
        print " ... You Pressed CTL+C, exit ... "

    elif _signal == signal.SIGHUP:
        print " ... get SIGHUP, exit ... "

    if _signal == signal.SIGTERM:
        print " ... get SIGTERM, exit ... "


#    db.dispose()

    # TODO: quit email
    try:
        qm = QueMail.get_instance()
        qm.end()
    except RuntimeError:
        pass

    sys.exit(1)


import mako
from mako.template import Template
from mako.lookup import TemplateLookup
mako.runtime.UNDEFINED = ''

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, '../template')
lookup = TemplateLookup([ TEMPLATE_DIR ], input_encoding="utf-8")

def render_template(template_name, **kwargs):

    t = lookup.get_template(template_name)

    args = dict()
    args.update(kwargs)

    try:
        html = t.render(**args)
    except:
        return None

    return html
    


import zmq
import time
import logging

import json

#logging.basicConfig(filename='myapp.log', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

def main():

    init_quemail()

    context = zmq.Context()  
    socket = context.socket(zmq.REP)  
    socket.bind("tcp://127.0.0.1:1368")
  
    while True:
        #  Wait for next request from client
        message = socket.recv()

        message = json.loads(message)
        logging.debug("Received request: %s" % message)

        #  Send reply back to client
        ret = {'code': 0, 'string': ''}
        ret_str = json.dumps( ret )
        socket.send( ret_str )

        logging.debug('reply message: %s' % ret_str)

        uri = message.get('uri', None)
        if not uri:
            logging.error( _('No uri in message.') )
            continue

        data = message.get('data', {})

        if uri == 'mailto.userlist':
            t = threading.Thread( target = mailto_user_list,
                                  args = (data,) )
            t.start()
#            mailto_user_list( data )

        elif uri == 'mailto.address':
            mailto_address( data )

        else:
            logging.error( _('Unsupported uri: %s') % uri )
            return

        # 
        #  Do some 'work'
        time.sleep (1)        #   Do some 'work'


if __name__ == '__main__':

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGHUP, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    try:
        main()
    finally:
        pass
