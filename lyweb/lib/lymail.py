# -*- coding:utf-8 -*-

import time
from smtplib import SMTP
from email.MIMEText import MIMEText
from email.Header import Header
from email.Utils import parseaddr, formataddr


admin_name     = 'Admin'
smtp_server    = None
smtp_port      = 25
email_from     = None
email_address  = None
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

if cf.has_option('email', 'address'):
    email_address = cf.get('email', 'address')

if cf.has_option('email', 'username'):
    email_username = cf.get('email', 'username')

if cf.has_option('email', 'password'):
    email_pass = cf.get('email', 'password')

if email_from and not email_address:
    email_address = email_from
if email_address and not email_from:
    email_from = email_address

if email_username and '@' in email_username:
    if not email_from:
        email_from = email_username
    if not email_address:
        email_address = email_username


def send_email(toaddr, subject, body, cc = [], bcc = []):

    global email_address, email_from, smtp_server, smtp_port, \
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
