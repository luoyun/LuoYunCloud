# coding: utf-8

from datetime import datetime
from lycustom import LyRequestHandler

from app.account.models import User, ApplyUser, UserProfile
from app.instance.models import Instance
from app.session.models import Session

from app.account.forms import LoginForm, ResetPasswordForm, \
    RegistrationForm

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

    ''' Show home of my '''

    @authenticated
    def get(self):

        my = self.db2.query(User).get(self.current_user.id)
        d = { 'my': my }

        show = self.get_argument('show', None)

        if not show: 
            d['title'] = _('My Account Center')
            self.render( 'account/index.html', **d)

        elif show == 'instances':
            d['title'] = _('My Instances')
            self.render( 'account/instances.html', **d)

        elif show == 'appliances':
            d['title'] = _('My Appliances')
            self.render( 'account/appliances.html', **d)

        elif show == 'groups':
            d['title'] = _('My Groups')
            self.render( 'account/groups.html', **d)

        elif show == 'permissions':
            d['title'] = _('My Permissions')
            self.render( 'account/permissions.html', **d)

        elif show == 'resources':
            self.get_resources(d)


    def get_resources(self, d):
        d['title'] = _('My Resources')
        insts = self.db2.query(Instance).filter(
            Instance.user_id == self.current_user.id )
        d['USED_INSTANCES'] = insts.count()
        d['USED_CPUS'] = 0
        d['USED_MEMORY'] = 0
        for i in insts:
            if i.status in [4, 5]:
                d['USED_CPUS'] += i.cpus
                d['USED_MEMORY'] += i.memory

        #print "d = ", d
        self.render( 'account/resources.html', **d)
            



class MyInstances(LyRequestHandler):

    @authenticated
    def get(self):

        user = self.db2.query(User).get(self.current_user.id)

        self.render( 'account/instances.html',
                     title = _('My Instances'),
                     INSTANCE_LIST = user.instances )


class MyGroups(LyRequestHandler):

    @authenticated
    def get(self):

        user = self.db2.query(User).get(self.current_user.id)

        self.render( 'account/instances.html',
                     title = _('My Instances') )



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

