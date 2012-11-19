# coding: utf-8

import os, json, Image, tempfile
from datetime import datetime
from lycustom import LyRequestHandler

from sqlalchemy.sql.expression import asc, desc

from app.account.models import User, ApplyUser, UserProfile, \
    UserResetpass, Group
from app.instance.models import Instance
from app.session.models import Session

from app.instance.models import Instance
from app.appliance.models import Appliance
from app.message.models import Message, MessageText

from app.account.forms import LoginForm, ResetPasswordForm, \
    RegistrationForm, AvatarEditForm, ResetPasswordApplyForm

import random, time, pickle, base64
from hashlib import md5, sha512, sha1

import tornado
from tornado.web import authenticated, asynchronous

from app.account.utils import encrypt_password, check_password

from lymail import send_email

from lycustom import has_permission

from lytool.filesize import size as human_size


import settings
from app.system.models import LuoYunConfig

from ytool.password import check_login_passwd, enc_login_passwd, \
    enc_shadow_passwd

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
                    user.last_login = datetime.now()
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
                enc_password = enc_login_passwd(form.password.data)
                newuser = User( username = form.username.data,
                                password = enc_password )
                self.db2.add(newuser)
                self.db2.commit()
                # Create profile
                profile = UserProfile(newuser, email = form.email.data)
                root_passwd = enc_shadow_passwd(form.password.data)
                profile.set_secret('root_shadow_passwd', root_passwd)
                # Add to default group
                from settings import cf
                if cf.has_option('registration', 'user_default_group_id'):
                    try:
                        DGID = int(cf.get('registration', 'user_default_group_id'))
                        G = self.db2.query(Group).get(DGID)
                        newuser.groups = [G]
                        self.db2.commit()
                    except:
                        pass

                self.db2.add(profile)
                self.db2.commit()

                # send_message
                self.send_message( newuser )

                # send_mail()

                self.save_session(newuser.id)

                return self.redirect( self.reverse_url('account:index') )

        # Have a error
        self.render( 'account/register.html', form = form )


    def send_message(self, user):
        admin = self.db2.query(User).filter_by(username='admin').first()
        if admin:

            welcome = self.db2.query(LuoYunConfig).filter_by(key='welcome_new_user').first()

            if welcome:
                wc = json.loads(welcome.value).get('text')

                T = MessageText(
                    subject = _('Welcome to use LuoYun Cloud !'),
                    body = wc )
                self.db2.add(T)
                self.db2.commit()

                M = Message( sender_id = admin.id,
                             receiver_id = user.id, text_id = T.id )

                self.db2.add(M)

                user.notify()
                self.db2.commit()



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

        by = self.get_argument('by', 'updated')
        sort = self.get_argument('sort', 'desc')

        if by == 'created':
            by_obj = Instance.created
        elif by == 'updated':
            by_obj = Instance.updated
        else:
            by_obj = Instance.id

        sort_by_obj = desc(by_obj) if sort == 'desc' else asc(by_obj)

        instances = self.db2.query(Instance).filter_by(
            user_id = id ).filter(
            Instance.isprivate != True ).order_by( sort_by_obj )

        total = instances.count()
        instances = instances.slice(0, 20).all() # TODO: show only

        d = { 'title': _('View User %s') % user.username,
              'USER': user, 'INSTANCE_LIST': instances,
              'TOTAL_INSTANCE': total }

        self.render( 'account/view_user.html', **d )



class ViewGroup(LyRequestHandler):

    @authenticated
    def get(self, gid):

        group = self.db2.query(Group).get(gid)

        if not group:
            return self.write(_('No such group: %s !') % gid)

        users = self.db2.query(User).filter(
            User.groups.contains(group) )

        total = users.count()

        users = users.slice(0, 20).all() # TODO: show only

        d = { 'title': _('View Group %s') % group.name,
              'GROUP': group, 'USER_LIST': users,
              'TOTAL_USER': total }

        self.render( 'account/view_group.html', **d )



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
            user = self.current_user
            enc_password = enc_login_passwd(form.password.data)
            user.password = enc_password

            root_passwd = enc_shadow_passwd(form.password.data)
            print 'root_passwd = ', root_passwd
            user.profile.set_secret('root_shadow_passwd', root_passwd)

            self.db2.commit()
            print 'secret = ', user.profile.get_secret()

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

        homedir = self.current_user.homedir
        if not os.path.exists(homedir):
            try:
                os.makedirs(homedir)
            except Exception, e:
                return _('Create user home dir "%s" failed: %s') % (homedir, e)

        max_size = settings.USER_AVATAR_MAXSIZE
        avatar_name = settings.USER_AVATAR_NAME

        for f in self.request.files['avatar']:

            if len(f['body']) > max_size:
                return _('Avatar file must smaller than %s !') % human_size(max_size)

            tf = tempfile.NamedTemporaryFile()
            tf.write(f['body'])
            tf.seek(0)

            try:
                img = Image.open( tf.name )

            except Exception, e:
                return _('Open %s failed: %s , is it a picture ?') % (f.get('filename'), e)

            try:
                img.save(self.current_user.avatar_orig_path)
                img.thumbnail(settings.USER_AVATAR_THUM_SIZE, resample=1)
                img.save(self.current_user.avatar_path)
                img.thumbnail(settings.USER_AVATAR_MINI_THUM_SIZE, resample=1)
                img.save(self.current_user.avatar_path)
                tf.close()

            except Exception, e:
                return _('Save %s failed: %s') % (f.get('filename'), e)



class ResetPasswordApply(LyRequestHandler):

    ''' Apply to reset password '''

    EMAIL_TEMPLATE = _('''
Reset Password for Your LuoYun Cloud Account.

Click the url to complete : %(URL)s

If you can not click the link above, copy and paste it on your brower address.
''')


    def get(self):

        d = { 'title': _('Forget My Password') ,
              'form': ResetPasswordApplyForm() }

        self.render( 'account/reset_password_apply.html', **d )


    def post(self):

        form = ResetPasswordApplyForm(self.request.arguments)

        if form.validate():

            profile = self.db2.query(UserProfile).filter(
                UserProfile.email == form.email.data ).first()

            if profile:

                # check exist request
                exist = self.db2.query(UserResetpass).filter_by(
                    user_id = profile.user.id ).all()
                exist = [ x for x in exist if not x.completed ]
                if exist:
                    RQ = exist[0]
                else:
                    RQ = UserResetpass( profile.user )
                    self.db2.add( RQ )
                    self.db2.commit()

                # send email
                from settings import cf
                if cf.has_option('site', 'home'):
                    SITE_HOME = cf.get('site', 'home').rstrip('/')
                else:
                    SITE_HOME = 'http://127.0.0.1'

                url = self.reverse_url('reset_password_complete')
                url = SITE_HOME + url + '?key=%s' % RQ.key

                ret = send_email(form.email.data, _('[ LuoYun Cloud ] Reset Password'), self.EMAIL_TEMPLATE % { 'URL': url } )

                if ret:
                    return self.render( 'account/reset_password_apply_successed.html', APPLY = RQ )
                else:
                    return self.write( _('Send Email Failed !') )

            else:
                form.email.errors.append( _("No such email address: %s") % form.email.data )

        d = { 'title': _('Reset Password'), 'form': form }

        self.render( 'account/reset_password_apply.html', **d )



class ResetPasswordComplete(AccountRequestHandler):

    ''' Apply to reset password '''

    def prepare(self):

        key = self.get_argument('key', None)
        if not key:
            self.write('No Key !')
            return self.finish()

        print 'key = ', key
        applys = self.db2.query(UserResetpass).filter(
            UserResetpass.key == key ).all()

        print 'applys = ', applys
        d = { 'title': _('Forget My Password') , 'ERROR': None,
              'USER': None }

        if applys:

            for A in applys:
                # TODO
                #d['ERROR'] = _('The validity period for a certificate has passed')
                if not A.completed:
                    d['USER'] = A.user
                    break

            if not d['USER']:

                d['ERROR'] = _('You have completed reset password.')

        else:
            d['ERROR'] = _('No such key: %s !') % key

        if d['ERROR']:
            self.render( 'account/reset_password_complete.html', **d )
            return self.finish()

        self.d = d
        self.key = key


    def get(self):
        self.d['form'] = ResetPasswordForm()
        self.render( 'account/reset_password_complete.html', **self.d )

    def post(self):
        self.d['form'] = ResetPasswordForm( self.request.arguments )
        if self.d['form'].validate():

            plaintext = self.d['form'].password.data
            enc_password = enc_login_passwd(plaintext)
            self.d['USER'].password = enc_password

            root_passwd = enc_shadow_passwd(plaintext)
            self.d['USER'].profile.set_secret('root_shadow_passwd', root_passwd)

            self.db2.commit()

            # TODO: set reset password request completed
            applys = self.db2.query(UserResetpass).filter(
                UserResetpass.key == self.key ).all()
            for A in applys:
                A.completed = datetime.now()
            self.db2.commit()

            self.save_session( self.d['USER'].id )

            url = self.reverse_url('account:index')
            return self.redirect( url )

        self.render( 'account/reset_password_complete.html', **self.d )



class Delete(LyRequestHandler):
    ''' Delete User '''

    @has_permission('admin')
    def get(self, id):

        d = { 'title': _('Delete Account'), 'ERROR': [], 'USER': None }

        user = self.db2.query(User).get(id)

        if user:
            d['USERNAME'] = user.username
            if user.id == self.current_user.id:
                d['ERROR'].append(_('You can not delete yourself!'))
            if user.instances:
                d['ERROR'].append(_('User "%s" have instances exist, please remove them first.') % user.username)
            if user.appliances:
                d['ERROR'].append(_('User "%s" have appliances exist, please remove them first.') % user.username)
        else:
            d['ERROR'].append(_('Have not found user by id %s') % id)

        if not d['ERROR']:

            # delete message
            from sqlalchemy import or_
            messages = self.db2.query(Message).filter(
                or_(Message.receiver_id == user.id,
                    Message.sender_id == user.id) )
            for M in messages:
                self.db2.delete(M)

            self.db2.delete( user )
            self.db2.commit()
        else:
            if user:
                d['USER'] = user

        self.render( 'account/delete.html', **d )



class islockedToggle(LyRequestHandler):
    ''' Toggle islocked flag '''

    @has_permission('admin')
    def get(self, ID):

        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        ID = int(ID)

        if self.current_user.id == ID:
            return self.write( _('You can not lock yourself !') )

        U = self.db2.query(User).get(ID)

        if U:
            U.islocked = not U.islocked
            self.db2.commit()
            # no news is good news

        else:
            self.write( _('Can not found the user.') )

