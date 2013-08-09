# -*- coding:utf-8 -*-

import os, time, logging, ConfigParser
from smtplib import SMTP
from email.MIMEText import MIMEText
from email.Header import Header
from email.Utils import parseaddr, formataddr

import settings

default_option = 'mail'

class MailConfig:

    def __init__(self):
        self.cf = None
        self._load()

    def _load(self):
        if ( hasattr(settings, 'sitecfg') and 
             os.path.exists( settings.sitecfg ) ):
            self.cf = ConfigParser.ConfigParser()
            self.cf.read( settings.sitecfg )
        else:
            logging.error('read sitecfg failed: %s not exist!' % settings.sitecfg)

    def get(self, key, default=None):

        if not self.cf: return default

        if settings.sitecfg_changed:
            self._load()

        if self.cf.has_option(default_option, key):
            return self.cf.get(default_option, key)
        else:
            return default

    def get_int(self, key, default=0):

        v = self.get(key, default)
        try:
            v = int(v)
        except:
            v = default
        return v

cf = MailConfig()
header_charset = 'ISO-8859-1'
body_charset = 'UTF-8'

def safe_mailaddr(addr):

    name, addr = parseaddr(addr)
    return formataddr( (
            str(Header(unicode(name), header_charset)),
            addr.encode('ascii') ) )


def sendmail( to, subject, body, cc = [], bcc = [],
              body_format='html',
              smtp_server = None,
              smtp_port = None,
              username = None,
              password = None,
              fromaddr = None ):

    if not ( isinstance(to, list) and
             isinstance(cc, list) and
             isinstance(bcc, list) ):
        logging.error('sendmail failed: to, cc, bcc must be a list')
        return False

    server = smtp_server if smtp_server else cf.get('smtp_server', 'localhost')
    port = smtp_port if smtp_port else cf.get_int('smtp_port', 25)
    fromaddr = fromaddr if fromaddr else cf.get('from', 'admin@localhost')
    username = username if username else cf.get('username')
    password = password if password else cf.get('password')

    msg = MIMEText(body.encode(body_charset), body_format, body_charset)

    msg['From'] = safe_mailaddr(fromaddr)
    msg['To']   = ', '.join([safe_mailaddr(x) for x in to])
    msg['CC']   = ', '.join([safe_mailaddr(x) for x in cc])
    msg['BCC']  = ', '.join([safe_mailaddr(x) for x in bcc])

    msg['Subject'] = Header(unicode(subject), header_charset)
    msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')

    try:
        port = int(port)
        smtp = SMTP(server, port)

        #smtp.ehlo()

        if server.endswith('gmail.com'):
            smtp.starttls()

        #smtp.ehlo()

        if ( username and password and 
             ( not server.endswith('127.0.0.1') ) and 
             ( not server.endswith('localhost') ) ):
            smtp.login(username, password)

        #print 'to = %s, cc = %s, bcc = %s' % (to, cc, bcc)
        smtp.sendmail(fromaddr, to + cc + bcc, msg.as_string())
        smtp.quit()
        return True

    except Exception, e:
        logging.error( 'sendmail failed: %s' % e )


import re
def validate_email(email):

    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return 1

    return 0

