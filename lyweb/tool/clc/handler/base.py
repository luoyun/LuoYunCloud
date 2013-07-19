import os
import pickle
import time
import logging
import random
from lyc.handler import TCPStreamHandler
from handler.node import NodeStreamHandler

from lyc.security import get_enc_password, check_password


class NewClientHandler(TCPStreamHandler):

    def data_received(self, data):

        time.sleep(1)

        if data['key'] == '/node/register':
            logging.debug('client was come from node')
            self._register_node(data)

        # TODO:
        elif data['key'] == 'mailto.userlist':
            t = threading.Thread( target = mailto_user_list,
                                  args = (data,) )
            t.start()

        elif data['key'] == 'mailto.address':
            mailto_address( data )

        else:
            logging.error('unknown key = %s, body = %s', data['key'], data)
            return self._handle_close()

    def _register_node(self, data):
        password = data['msg'].get('password')
        enc = get_enc_password('fffaaa')
        if check_password(password, enc):
            self.stream.send_msg(msg={'status': True}, key='/register/result')
        else:
            logging.error('authorized for node client failed, close connection.')
            self.stream.send_msg(msg={'status': False}, key='/register/result')
            return self._handle_close()

        h = NodeStreamHandler( self.application, self.sock, self.ioloop,
                               client_address=self.client_address )

        node_id = int((random.random() * 100) / 2)
        node_data = {'name': 'testnode03'}
        self.application.nodes.append( (node_id, node_data) )
        self.registered = True

        self.ioloop.remove_handler(self.sock.fileno())
        self.ioloop.add_handler(self.sock.fileno(), h, self.ioloop.READ)
        logging.info('node registered success')


# TODO:
# =================== TEMP NOW ====================
import threading

from app.auth.models import User
from app.site.models import SiteJob, SiteConfig
from yweb import orm


from yweb.quemail import Email
def mailto_user_list( data ):

    data = data.get('msg', {})
#    logging.debug('mailto_user_list: data = %s' % data)

    dbsession = orm.create_session()
    db = dbsession()

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

    if UID_LIST:
        USER_LIST = []
        for ID in UID_LIST:
            U = db.query(User).get( ID )
            if U:
                USER_LIST.append( U )
    else:
        USER_LIST = db.query(User)

    mail_total = SiteConfig.get( db, 'site.send_mail.total', 0 )
    if not mail_total:
        SiteConfig.set(db, 'site.send_mail.total', 0)

    mail_total = db.query(SiteConfig).filter_by(
        key = 'site.send_mail.total').first()

    fm = FileSysMail.get_instance()

    for U in USER_LIST:

        text = _('send mail to %s: %s (%s)') % (U.id, U.username, U.email)

        logging.debug( text )

        job.update_status( text )
        db.commit()

#        time.sleep(1)

        if not (U and U.email and U.email_valid):
            continue

        d = { 'subject': subject, 'BODY_HTML': body,
              'username': U.nickname if U.nickname else U.username }

        body_html = render_template('custom/mail_template.html', **d)

        if body_html:

            e = Email( subject = subject, text = body_html,
                       adr_to = U.email,
                       adr_from = adr_from, mime_type = 'html' )

            mail_total.value = int(mail_total.value) + 1
            fm.send( e, '%s-mail' % mail_total.value )

        else:
            logging.error( _('render email body for html failed.') )

    job.set_ended()
    db.commit()
    dbsession.remove()


def mailto_address( data ):

    data = data.get('msg', {})
#    logging.debug('mailto_address: data = %s' % data)

    dbsession = orm.create_session()
    db = dbsession()

    to = data.get('to', None)
    to_user_id = data.get('to_user_id', None)
    subject = data.get('subject', None)
    body = data.get('body', None)
    adr_from = SiteConfig.get(
        db, 'notice.smtp.fromaddr', 'admin@localhost')

    if not (to or to_user_id):
        logging.error( _('mailto_address: no address find') )
        return

    mail_total = SiteConfig.get( db, 'site.send_mail.total', 0 )
    if not mail_total:
        SiteConfig.set(db, 'site.send_mail.total', 0)

    mail_total = db.query(SiteConfig).filter_by(
        key = 'site.send_mail.total').first()

    fm = FileSysMail.get_instance()

    if to:
        username = to.split('@')[0]

    if to_user_id:
        U = db.query(User).get( to_user_id )
        if U:
            username = U.nickname if U.nickname else U.username
            to = U.email
            if not to:
                logging.error( _('mailto_address: %s(%s) have not email address') % (username, U.id) )
                return


    d = { 'subject': subject, 'BODY_HTML': body,
          'username': username }

    body = render_template('custom/mail_template.html', **d)

    if body:
        e = Email( subject = subject, text = body,
                   adr_to = to,
                   adr_from = adr_from, mime_type = 'html' )

        mail_total.value = int(mail_total.value) + 1
        fm.send( e, '%s-mail' % mail_total.value )

    else:
        logging.error( _('render email body for html failed.') )



import mako
from mako.template import Template
from mako.lookup import TemplateLookup
mako.runtime.UNDEFINED = ''

CUR_ROOT = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(CUR_ROOT, '../../../template')
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


from yweb.mail import FileSysMail
def start_filesysmail():

    dbsession = orm.create_session()
    db = dbsession()

    fm = FileSysMail.get_instance()

    smtp_server = SiteConfig.get(
        db, 'notice.smtp.server', '127.0.0.1')
    smtp_port = int(SiteConfig.get(
            db, 'notice.smtp.port', 25 ))
    smtp_username = SiteConfig.get(
        db, 'notice.smtp.username', None)
    smtp_password = SiteConfig.get(
        db, 'notice.smtp.password', None)

    mail_dir = SiteConfig.get(
        db, 'site.send_mail.dir', '/opt/LuoYun/run/email/')

    print 'smtp_server   = ', smtp_server
    print 'smtp_port     = ', smtp_port
    print 'smtp_username = ', smtp_username
    print 'smtp_password = ', smtp_password

    fm.init( smtp_server, smtp_username, smtp_password,
             smtp_port = smtp_port, store_path = mail_dir )

    fm.start()

    dbsession.remove()
