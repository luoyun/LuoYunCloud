# -*- coding: utf-8 -*-
# https://github.com/marcinc81/quemail/blob/master/quemail.py

# Updater: Jian <lijian@luoyun.co>


import os
import smtplib
import logging
import time
import pickle

from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate

from time import sleep
from threading import Thread

log = logging.getLogger("LYMail")


class Email(object):
    unique = 'unique-send'
    
    def __init__(self, **props):
        '''
        @param adr_to: send to
        @param adr_from: send from
        @param subject: subject of email
        @param mime_type: plain or html - only minor mime type of 'text/*'
        @param text: text content of email
        ''' 
        self.text = props.get('text', '')
        self.subject = props.get('subject', None)
        self.adr_to = props.get('adr_to', None)
        self.adr_from = props.get('adr_from', None)
        self.mime_type = props.get('mime_type', 'plain')
        
    def __str__(self):
        return "Email to: %s, from: %s, sub: %s" % (self.adr_to, self.adr_from, self.subject)

    def as_rfc_message(self):
        '''
        Creates standardized email with valid header
        '''
        msg = MIMEText(self.text, self.mime_type, 'utf-8')
        msg['Subject'] = self.subject
        msg['From'] = self.adr_from
        msg['To'] = self.adr_to
        msg['Date'] = formatdate()
        msg['Reply-To'] = self.adr_from
        msg['Message-Id'] = make_msgid(Email.unique)
        return msg


class DummyMail(object):

    instance = None

    def send(self, eml):
        log.error('config of send email is wrong.')

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = DummyMail()
        return cls.instance


class FileSysMail(Thread):

    '''Send mail by file system.

    1. send method , store mail to file system

    2. run , loop , send mail while mail exists in file system
    '''

    instance = None

    def init(self, smtp_host, smtp_login=None, smtp_pswd=None,
             smtp_port=25, store_path='/opt/LuoYun/run/email/'):

        log.info("Initializing FileSysMail with SMTP server: %s:%i." % (smtp_host, smtp_port))

        if not os.path.exists( store_path ):
            try:
                os.makedirs( store_path )
            except Exception, e:
                logging.error('Can not create store dir "%s": %s' % (store_path, e))
                return False

        self.store_path = store_path
        self.smtp_host = smtp_host
        self.smtp_login = smtp_login
        self.smtp_password = smtp_pswd
        self.smtp_port = smtp_port

        return True

    
    def __init__(self):
        Thread.__init__(self)
        self._do_quit = False
        self.setName("FileSysMail")
        self.smtp_host = None
        self.smtp_login = None
        self.smtp_password = None
#        self.smtp_port = None
#        self.store_path = None
        self.check_interval = 3   # the number of seconds to check the filesystem

    def end(self):
        '''
        Waits until all emails will be sent and after that stops thread
        '''
        log.info("Stopping QueMail thread...")
        self.check_interval = 1
        self._do_quit = True
        self.join()
        log.info("Stopped.")

    def get_email(self, filename):

        fpath = os.path.join( self.store_path, filename )
        f = open(fpath, 'r')
        eml = pickle.load(f)
        f.close()

        return eml

    def delete_email(self, filename):

        fpath = os.path.join( self.store_path, filename )

        try:
            os.unlink( fpath ) # delete email
        except Exception, e:
            logging.error('delete %s failed: %s' % (fpath, e))


    def run(self):
        while not self._do_quit:

            email_list = os.listdir( self.store_path )

            if not email_list:
                sleep(self.check_interval)
                continue

            log.debug(u"Connecting to SMTP server: %s:%i" % (self.smtp_host, self.smtp_port))
            smtp = None
            try:
                smtp = smtplib.SMTP()
                smtp.connect(self.smtp_host, self.smtp_port)
                if self.smtp_login and self.smtp_password:
                    smtp.login(self.smtp_login, self.smtp_password)
    
                while email_list:
                    t = time.time()
                    filename = email_list.pop()
                    eml = self.get_email( filename )
                    log.info(u"Sending %s: %s" % ( filename, eml ))
                    try:
                        msg = eml.as_rfc_message()
                        content = msg.as_string()
                        smtp.sendmail(eml.adr_from, eml.adr_to, content)
                        logging.debug('Send mail to %s success' % eml.adr_to)
                    except Exception as e:
                        log.error(u"Exception occured while sending email: %s" % eml)
                        log.exception(e)
                        # FIXME not good idea: when exception occured, add email at end of queue
                        # Jian: TODO
                        #self._queue.put(eml, False)
                        #sleep(1)

                    self.delete_email( filename )

            except Exception as e:
                log.exception(e)
            finally:
                if smtp:
                    smtp.quit()

        
    def send(self, eml, store_name):

        p = os.path.join(self.store_path, store_name)
        f  = open(p, 'w')
        pickle.dump(eml, f)
        f.close()

        log.debug(u'Accepted mail %s' % eml)

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = FileSysMail()
        return cls.instance
