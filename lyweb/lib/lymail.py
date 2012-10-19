# -*- coding:utf-8 -*-

import time, logging
from smtplib import SMTP
from email.MIMEText import MIMEText
from email.Header import Header
from email.Utils import parseaddr, formataddr


admin_name     = 'Admin'
smtp_server    = None
smtp_port      = 25
email_from     = None
email_username = None
email_pass     = None

from settings import cf

if cf.has_option('email', 'smtp_server'):
    smtp_server = cf.get('email', 'smtp_server')

if cf.has_option('email', 'smtp_port'):
    smtp_port = int( cf.get('email', 'smtp_port') )

if cf.has_option('email', 'name'):
    admin_name = cf.get('email', 'name')

if cf.has_option('email', 'from'):
    email_from = cf.get('email', 'from')

if cf.has_option('email', 'username'):
    email_username = cf.get('email', 'username')

if cf.has_option('email', 'password'):
    email_pass = cf.get('email', 'password')

if email_username and '@' in email_username:
    if not email_from:
        email_from = email_username


def send_email(toaddr, subject, body, cc = [], bcc = []):

    global email_from, smtp_server, smtp_port, \
        email_username, email_pass

    # TODO: something check
    if not smtp_server:
        return False

    fromaddr = email_from

    # Header class is smart enough to try US-ASCII, then the charset we
    # provide, then fall back to UTF-8.
    header_charset = 'ISO-8859-1'

    # We must choose the body charset manually
    for body_charset in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
        try:
            body.encode(body_charset)
        except UnicodeError:
            pass
        else:
            break

    from_name, from_addr = parseaddr(fromaddr)
    to_name, to_addr = parseaddr(toaddr)

    from_name = str(Header(unicode(from_name), header_charset))
    to_name = str(Header(unicode(to_name), header_charset))

    from_addr = from_addr.encode('ascii')
    to_addr = to_addr.encode('ascii')

    msg = MIMEText(body.encode(body_charset), 'plain', body_charset)
    msg['From'] = formataddr((from_name, from_addr))
    msg['To'] = formataddr((to_name, to_addr))

    if cc:
        L = []
        for x in cc:
            x_name, x_addr = parseaddr(x)
            L.append( formataddr((x_name, x_addr)) )
        msg['CC'] = ', '.join(L)

    if bcc:
        L = []
        for x in bcc:
            x_name, x_addr = parseaddr(x)
            L.append( formataddr((x_name, x_addr)) )
        msg['BCC'] = ', '.join(L)

    msg['Subject'] = Header(unicode(subject), header_charset)
    msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')

    toaddrs = [toaddr] + cc + bcc

    smtp = SMTP(smtp_server, smtp_port)
    #smtp.ehlo()
    #smtp.starttls()
    #smtp.ehlo()
    smtp.login(email_username, email_pass)
    smtp.sendmail(fromaddr, toaddrs, msg.as_string())
    smtp.quit()
    return True


class LyMail:

    global email_from, smtp_server, smtp_port, \
        email_username, email_pass

    header_charset = 'ISO-8859-1'

    def __init__( self, host = smtp_server, port = smtp_port,
                  username = email_username,
                  password = email_pass,
                  fromaddr = email_from,
                  HTML = False ):

        self.host      = host
        self.port      = port
        self.username  = username
        self.password  = password
        self.fromaddr = fromaddr
        self.HTML      = HTML
        self.server    = None

    def connect(self):

        try:

            s = SMTP( self.host, self.port )
            s.login( self.username, self.password )
            self.server = s
            return True

        except Exception, e:
            logging.error( 'Connect to %s:%s failed: %s' % (
                    self.host, self.port, e) )
            return False


    def sendmail(self, toaddr, subject, body, cc=[], bcc=[]):

        if not self.server:
            self.connect()

        logging.info( 'Send mail to %s' % toaddr )

        for body_charset in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
            try:
                body.encode(body_charset)
            except UnicodeError:
                pass
            else:
                break

        from_name, from_addr = parseaddr( self.fromaddr )
        to_name  , to_addr   = parseaddr( toaddr )

        from_name = str(Header(unicode(from_name), self.header_charset))
        to_name = str(Header(unicode(to_name), self.header_charset))

        from_addr = from_addr.encode('ascii')
        to_addr = to_addr.encode('ascii')

        if from_addr == to_addr:
            logging.info( 'Send mail to myself is not allowed now.')
            return

        email_format = 'html' if self.HTML else 'plain'
            
        msg = MIMEText( body.encode(body_charset), email_format, body_charset )
        msg['From'] = formataddr((from_name, from_addr))
        msg['To'] = formataddr((to_name, to_addr))

        if cc:
            msg['CC'] = ', '.join([ self._formataddr(x) for x in cc ])

        if bcc:
            msg['BCC'] = ', '.join([ self._formataddr(x) for x in bcc ])

        msg['Subject'] = Header(unicode(subject), self.header_charset)
        msg['date'] = time.strftime('%a, %d %b %Y %H:%M:%S %z')

        try:
            self.server.sendmail( self.fromaddr, [toaddr] + cc + bcc, msg.as_string() )
        except Exception, e:
            logging.error( 'Send mail from %s:%s to %s failed: %s' % (
                    self.host, self.port, toaddr, e) )

    def close(self):
        if self.server:
            self.server.close()


    def _formataddr(self, addr):
        x_name, x_addr = parseaddr( addr )
        x_name = str(Header(unicode(x_name), self.header_charset))
        x_addr.encode('ascii')
        return formataddr((x_name, x_addr))


import re
def validate_email(email):

    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return 1

    return 0



if __name__ == '__main__':

    lymail = LyMail()

    lymail.connect()

    subject = u'Test From LuoYunCloud Mail System'
    body = u'Use LuoYunCloud Mail System, It is worked !'

    for toaddr in ['lijian@ylinux.org', 'lijian@luoyun.co']:
        lymail.sendmail(toaddr, subject, body)

    lymail.close()
