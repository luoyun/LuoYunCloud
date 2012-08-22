# coding: utf-8

import os
from datetime import datetime
from lycustom import LyRequestHandler

from app.account.models import User, ApplyUser, UserProfile
from app.instance.models import Instance
from app.session.models import Session

from app.instance.models import Instance
from app.appliance.models import Appliance

from app.account.forms import LoginForm, ResetPasswordForm, \
    RegistrationForm, AvatarEditForm

import random, time, pickle, base64
from hashlib import md5, sha512, sha1

import tornado
from tornado.web import authenticated, asynchronous

from app.account.utils import encrypt_password, check_password


import settings



class AccountRequestHandler(LyRequestHandler):


    def save_session(self, user_id):
        self.require_setting("cookie_secret", "secure cookies")

        session_key = sha1('%s%s' % (random.random(), time.time())).hexdigest()
        self.set_secure_cookie('session_key', session_key)

        session_dict = {'user_id': user_id}
        sk = self.application.settings["session_secret"]
        pickled = pickle.dumps(session_dict, pickle.HIGHEST_PROTOCOL)
        pickled_md5 = md5(pickled + sk).hexdigest()
        session_data = base64.encodestring(pickled + pickled_md5)

        session = Session(session_key, session_data)
        self.db2.add(session)
        self.db2.commit()



    def delete_session(self, user_id):
        session_key = self.get_secure_cookie('session_key')

        session = self.db2.query(Session).filter_by(
            session_key = session_key).first()
        self.db2.delete(session)
        self.db2.commit()

        self.clear_all_cookies()



class Login(AccountRequestHandler):


    def get(self):
        form = LoginForm()
        self.render("account/login.html", form=form,
                    next_url = self.get_argument('next', '/'))

    def post(self):

        form = LoginForm(self.request.arguments)
        if form.validate():
            user = self.db2.query(User).filter_by(username=form.username.data).first()
            if user:
                if user.islocked:
                    form.password.errors.append( _('You have been lock by admin, can not login now. If you have any questions, contact admin first please !') )
                    return self.render('account/login.html', form=form)

                if check_password(form.password.data, user.password):
                    self.save_session(user.id)
                    user.last_login = datetime.utcnow()
                    self.db2.commit()
                    return self.redirect( self.get_argument('next', '/') )
                else:
                    form.password.errors.append( _('password is wrong !') )
            else:
                form.username.errors.append( _('No such user !') )

        self.render('account/login.html', form=form)



class Logout(AccountRequestHandler):
    @authenticated
    def get(self):
        if self.current_user:
            self.delete_session(self.current_user.id)
            self.redirect('/')
        else:
            d['username_error'] = 'Have not found user.'
            self.render('account/login.html', **d)



# TODO: No used now
class Register(AccountRequestHandler):

    ''' Complete a Registration '''


    def initialize(self):

        self.enable_apply = False
        self.key = self.get_argument('key', None)
        self.applyuser = None

        if hasattr(settings, 'REGISTRATION_APPLY'):
            self.enable_apply = settings.REGISTRATION_APPLY

        if self.key:
            self.applyuser = self.db2.query(Applyuser).filter_by(
                key = self.key).one()


    def get(self):

        if self.enable_apply:
            if not self.key:
                return self.write( _('No key found !') )
            if not self.applyuser:
                return self.write( _('No apply record found !') )

        form = RegistrationForm()
        if self.applyuser:
            form.email.data = self.applyuser.email

        self.render( 'account/register.html', form = form )


    def post(self):

        form = RegistrationForm(self.request.arguments)

        if form.validate():

            user = self.db2.query(User).filter_by( username=form.username.data ).all()

            if user:
                form.username.errors.append( _('This username is occupied') )
            else:
                salt = md5(str(random.random())).hexdigest()[:12]
                hsh = encrypt_password(salt, form.password.data)
                enc_password = "%s$%s" % (salt, hsh)

                newuser = User( username = form.username.data,
                                password = enc_password )
                self.db2.add(newuser)
                self.db2.commit()
                # Create profile
                profile = UserProfile(newuser, email = form.email.data)
                self.db2.add(profile)
                self.db2.commit()

                # send_mail()
                self.save_session(newuser.id)

                url = self.application.reverse_url('account:index')
                return self.redirect( url )

        # Have a error
        self.render( 'account/register.html', form = form )



# TODO:
class RegisterApply(AccountRequestHandler):


    def get(self):

        applyer = self.db2.query(Applyer).filter_by(key=key).one()

        if applyer:

            salt = md5(str(random.random())).hexdigest()[:12]
            hsh = encrypt_password(salt, password)
            enc_password = "%s$%s" % (salt, hsh)

            user = User( username = applyer.username,
                         password = enc_password )


    def post(self):

        applyer = ApplyUser( email = form.email.data,
                             ip = self.request.remote_ip )
        self.db2.add(applyuser)
        self.db2.commit()



class Index(LyRequestHandler):

    @authenticated
    def get(self):

        my = self.db2.query(User).get(self.current_user.id)
        d = { 'title': _('My Account Center'),
              'my': my }

        self.render( 'account/index.html', **d)


class MyPermission(LyRequestHandler):

    @authenticated
    def get(self):

        my = self.db2.query(User).get(self.current_user.id)
        d = { 'title': _('My Permissions'),
              'my': my }

        self.render( 'account/permissions.html', **d)



class ViewUser(LyRequestHandler):
    ''' Show home of specified user '''
    def get(self, id):

        user = self.db2.query(User).get(id)

        if not user:
            return self.write('Have not found user by id %s' % id)

        instances = self.db2.query(Instance).filter_by(user_id=id)

        self.render( 'account/view_user.html',
                     title = 'View User', user = user,
                     INSTANCE_LIST = instances )



class ResetPassword(LyRequestHandler):


    @authenticated
    def get(self):

        form = ResetPasswordForm()

        self.render( 'account/reset_password.html', title = _('Reset Password'),
                     form = form )


    @authenticated
    def post(self):

        form = ResetPasswordForm(self.request.arguments)

        if form.validate():

            salt = md5(str(random.random())).hexdigest()[:12]
            hsh = encrypt_password(salt, form.password.data)
            enc_password = "%s$%s" % (salt, hsh)

            user = self.db2.query(User).get( self.current_user.id )
            user.password = enc_password
            self.db2.commit()

            url = self.application.reverse_url('account:index')
            return self.redirect( url )

        self.render( 'account/reset_password.html', title = _('Reset Password'),
                     form = form )


class AvatarEdit(LyRequestHandler):

    @authenticated
    def get(self):
        form = AvatarEditForm()
        d = { 'title': _('Change my avatar'),
              'form': form }

        self.render( 'account/avatar_edit.html', **d )


    @authenticated
    def post(self):
        # Save logo file
        form = AvatarEditForm()

        if self.request.files:
            r = self.save_avatar()
            if r:
                form.avatar.errors = [ r ] # TODO: a tuple
            else:
                url = self.reverse_url('account:index')
                return self.redirect( url )

        d = { 'title': _('Change my avatar'),
              'form': form }
        self.render( 'account/avatar_edit.html', **d )


    def save_avatar(self):
        support_image = ['jpg', 'png', 'jpeg', 'gif', 'bmp']
        for f in self.request.files['avatar']:

            if len(f['body']) > 368640: # 360 K
                return _('Avatar file must smaller than 360K !')

            ftype = 'unknown'
            x = f['content_type'].split('/')
            if len(x) == 2:
                ftype = x[-1]
            else:
                x = f['filename'].split('.')
                if len(x) == 2:
                    ftype = x[-1]

            ftype = ftype.lower()

            if ftype not in support_image:
                return _('No support image, support is %s' % support_image )

            fpath = os.path.join( settings.STATIC_PATH,
                              'user/%s' % self.current_user.id )

            try:
                if not os.path.exists( fpath ):
                    os.mkdir( fpath )

                fpath = os.path.join( fpath, 'avatar' )

                savef = file(fpath, 'w')
                savef.write(f['body'])
                savef.close()
                break # Just one upload file

            except Exception, emsg:
                return emsg
