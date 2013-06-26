# coding: utf-8

import os
import datetime
import random
import time

from hashlib import sha1

from sqlalchemy import and_

import tornado
from tornado.web import authenticated, asynchronous

from ..auth.models import User
from ..account.views import AccountRequestHandler
from ..auth.utils import enc_login_passwd
from ..site.models import SiteConfig, SiteLocaleConfig

from .models import RegistrationApply
from .forms import RegistrationApplyForm, RegistrationForm

# TODO: drop account relationships
from app.account.models import UserProfile

from lycustom import RequestHandler


class Register(AccountRequestHandler):

    def prepare(self):

        sc = self.db.query(SiteConfig).filter_by(
            key = 'registration.status' ).first()

        if sc and sc.value != 'true':
            self.write( _('Registration is disabled now.') )
            return self.finish()

        key = self.get_argument('key', None)
        E = []

        if key:
            form = RegistrationForm(self)
            title = _('Complete the registration')
            template = "registration/registration.html"
            # check key
            x=self.db.query(RegistrationApply).filter_by(key=key).first()
            if x:
                self.exist_key = x
            else:
                E.append( _('key "%s"is not exist.') % key)

        else:
            form = RegistrationApplyForm(self)
            title = _('Registration Apply')
            template = "registration/apply.html"

        d = { 'form': form, 'title': title, 'E': E }

        if self.request.method.lower() == 'get' or E:
             return self.render(template, **d)

        self.d = d
        self.key = key
        self.template = template


    def post(self):

        if self.key:
            self.post_registration()
        else:
            self.post_apply()


    def post_apply(self):

        form = self.d['form']

        while True:
            if not form.validate(): break

            # check email
            K=self.db.query(RegistrationApply).filter_by(email=form.email.data).first()
            U=self.db.query(User).filter_by(email=form.email.data).first()
            if K:
                K.key = sha1(str(random.random())).hexdigest()
            elif U:
                form.email.errors.append( _('Email (%s) is alreay exist.') % form.email.data )
                break
            else:
                K = RegistrationApply(email = form.email.data)
                self.db.add(K)

            self.db.commit()
            # TODO: sendmail
            self.sendmail(K)
            return self.render('registration/apply_complete.html', **self.d)

        self.render(self.template, **self.d)


    def post_registration(self):

        form = self.d['form']

        if form.validate():
            old = self.db.query(User).filter_by(username=form.username.data).count()
            if old:
                form.username.errors.append( _('Username is occupied.'))
            else:
                encpass = enc_login_passwd(form.password.data)
                new = User( username = form.username.data,
                            password = encpass,
                            language = self.language )
                new.email_valid = True
                new.email = self.exist_key.email
                self.db.add(new)
                self.db.delete(self.exist_key)
                self.db.commit()

                # TODO: drop account relationships
                profile = UserProfile( new )
                self.db.add(profile)
                self.db.commit()

                new.init_account(self.db)

                self.save_session(new.id)
                return self.redirect('/')

        self.render(self.template, **self.d)


    def sendmail(self, _apply):

        host = SiteConfig.get(
            self.db, 'registration.host', 'http://127.0.0.1')

        subject = self.db.query(SiteLocaleConfig).filter(
            and_(SiteLocaleConfig.key == 'registration.email.subject',
                 SiteLocaleConfig.language_id == self.language.id)).first()
        if subject:
            subject = subject.value
        else:
            subject = _('Thanks for register our site.')

        welcome = self.db.query(SiteLocaleConfig).filter(
            and_(SiteLocaleConfig.key == 'registration.email.welcome',
                 SiteLocaleConfig.language_id == self.language.id)).first()
        welcome_html = welcome.html if welcome else ''

        url = host + '/register?key=%s' % _apply.key

        d = { 'return_string': True, 'APPLY': _apply,
              'REGISTER_URL': url, 'WELCOME': welcome_html }

        body = self.render('registration/apply_email.html', **d)

        adr_from = SiteConfig.get(self.db, 'notice.smtp.fromaddr',
                                  'localhost@localhost')

        from yweb.quemail import Email

        e = Email( subject=subject, text=body,
                   adr_to=_apply.email, adr_from=adr_from,
                   mime_type = 'html' )
 
        self.quemail.send( e )
