# coding: utf-8

import os
import json
import tempfile
import Image
import random, pickle, base64, time, datetime
from hashlib import sha1, md5


from sqlalchemy import and_

from tornado.web import authenticated, asynchronous
from lycustom import RequestHandler

from yweb.contrib.session.models import Session
from app.auth.models import User, Group, OpenID, AuthKey
from app.auth.utils import enc_login_passwd

from .models import UserResetpass, PublicKey, UserProfile
from .forms import LoginForm, ResetPassForm, ResetPassApplyForm, \
    BaseInfoForm, AvatarForm, PublicKeyForm, EmailValidateForm, \
    OpenIDNewForm


from app.site.models import SiteConfig, SiteLocaleConfig

from yweb.utils import randstring
from yweb.quemail import Email

import settings



class AccountRequestHandler(RequestHandler):

    def save_session(self, user_id):
        self.require_setting("cookie_secret", "secure cookies")

        session_key = sha1('%s%s' % (random.random(), time.time())).hexdigest()

        session_dict = {'user_id': user_id}
        sk = self.settings["session_secret"]
        pickled = pickle.dumps(session_dict, pickle.HIGHEST_PROTOCOL)
        pickled_md5 = md5(pickled + sk).hexdigest()
        session_data = base64.encodestring(pickled + pickled_md5)

        session = Session(session_key, session_data)
        self.db.add(session)
        self.db.commit()

        self.set_secure_cookie('session_key', session_key)


    def delete_session(self, user_id):
        session_key = self.get_secure_cookie('session_key')

        session = self.db.query(Session).filter_by(
            session_key = session_key).first()
        self.db.delete(session)
        self.db.commit()

        self.clear_all_cookies()



class Login(AccountRequestHandler):

    title = _('Welcome to Login')
    template_path = 'account/login.html'

    def prepare(self):

        self.prepare_kwargs['form'] = LoginForm(self)

    def get(self):
        self.render()

    def post(self):
        _ = self.trans

        form = self.prepare_kwargs['form']

        if form.validate():
            user = form.true_user
            self.save_session(user.id)
            user.last_login = datetime.datetime.now()
            self.db.add(user)
            self.db.commit()
            return self.redirect_next('/')

        self.render()


class Logout(AccountRequestHandler):

    @authenticated
    def get(self):
        self.delete_session(self.current_user.id)
        self.redirect('/')



class MyAccount(RequestHandler):

    @authenticated
    def get(self):

        self.render( 'account/index.html' )



class ResetPassApply(RequestHandler):

    title = _('Reset My Password Please')
    template_path = 'account/reset_password_apply.html'

    def get(self):

        self.render( form = ResetPassApplyForm(self) )

    def post(self):

        form = ResetPassApplyForm(self)

        if form.validate():
            user = self.db.query(User).filter_by(
                email = form.email.data.strip() ).first()
            if user:
                applys = self.db.query(UserResetpass).filter(
                    and_(UserResetpass.user_id == user.id,
                         UserResetpass.completed is None)).all()
                if len(applys):
                    for a in applys:
                        self.db.delete(a)

                new = UserResetpass(user)
                self.db.add(new)
                self.db.commit()

                self.sendmail( new )

                t = 'account/reset_password_apply_success.html'
                return self.render( t, user = user )
            else:
                form.email.errors.append( _("Unregistered Mail") )

        self.render( form = form )


    def sendmail(self, _apply):

        LID = self.language.id

        host = SiteConfig.get(
            self.db, 'site.host', 'http://127.0.0.1')

        subject = self.db.query(SiteLocaleConfig).filter(
            and_(SiteLocaleConfig.key == 'resetpass.email.subject',
                 SiteLocaleConfig.language_id == LID)).first()
        subject = subject.value if subject \
            else _('Reset your password.')

        
        url = host + self.reverse_url('account:resetpass') \
            + '?key=%s' % _apply.key

        d = { 'return_string': True, 'APPLY': _apply,
              'RESET_URL': url }

        body = self.render('account/reset_password_email.html', **d)

        adr_from = SiteConfig.get(self.db, 'notice.smtp.fromaddr',
                                  'localhost@localhost')

        e = Email( subject   = subject, text=body,
                   adr_to    = _apply.user.email,
                   adr_from  = adr_from,
                   mime_type = 'html' )
 
        self.quemail.send( e )



class ResetPass(AccountRequestHandler):

    title = _('Complete Reset Password')
    template_path = 'account/reset_password.html'

    def prepare(self):
        key = self.get_argument('key', None)
        if key:
            it = self.db.query(UserResetpass).filter_by(
                key = key ).first()
            if it:
                self.user_apply = it
                self.user = it.user
                return

        d = { 'emsg': _('No such key: %s') % key }
        return self.render('account/reset_password_failed.html', **d)


    def get(self):
        d = { 'form': ResetPassForm(self), 'user': self.user }
        return self.render( **d )

    def post(self):

        form = ResetPassForm(self)

        if form.validate():
            self.user.password = enc_login_passwd(form.password.data)
            self.db.add( self.user )
            self.db.delete( self.user_apply )
            self.db.commit()
            self.save_session( self.user.id )
            return self.redirect('/')

        d = { 'form': form, 'user': self.user }
        self.render( **d )


class ResetMyPass(AccountRequestHandler):

    title = _('Reset My Password')
    template_path = 'account/reset_mypass.html'

    @authenticated
    def get(self):
        return self.render( form = ResetPassForm(self) )

    @authenticated
    def post(self):

        form = ResetPassForm(self)

        if form.validate():
            self.current_user.password = enc_login_passwd(form.password.data)
            self.db.add( self.current_user )
            self.db.commit()
            return self.redirect('/account')

        self.render( form = form )



class BaseInfoEdit(RequestHandler):

    title = _('Edit Base Information Of My Account')
    template_path = 'account/baseinfo_edit.html'

    @authenticated
    def prepare(self):

        self.language_list = []
        for L in self.application.supported_languages_list:
            self.language_list.append( (str(L.id), L.name) )

        self.user = self.db.query(User).get( self.current_user.id )

    def get(self):

        form = BaseInfoForm(self)
        form.language.choices = self.language_list
        form.language.default = self.user.language_id
        form.process()

        form.nickname.data = self.user.nickname
        form.first_name.data = self.user.first_name
        form.last_name.data = self.user.last_name

        self.render( form = form )


    def post(self):
        form = BaseInfoForm(self)
        form.language.choices = self.language_list

        if form.validate():
            self.user.nickname = form.nickname.data.strip()
            self.user.first_name = form.first_name.data.strip()
            self.user.last_name = form.last_name.data.strip()
            self.user.language_id = form.language.data
            self.db.add( self.user )
            self.db.commit()

            return self.redirect( '/account' )

        self.render( form = form )



class AvatarEdit(RequestHandler):

    title = _('Edit My Avatar')
    template_path = 'account/avatar_edit.html'

    @authenticated
    def get(self):
        self.render( form = AvatarForm(self) )


    @authenticated
    def post(self):
        form = AvatarForm(self)

        if self.request.files and form.validate():
            r = self.save_avatar()
            if r:
                form.avatar.errors.append( r )
            else:
                return self.redirect( '/account' )

        self.render( form = form )


    def save_avatar(self):

        homedir = self.current_user.homedir
        if not os.path.exists(homedir):
            try:
                os.makedirs(homedir)
            except Exception, e:
                return _('Create "%(dir)s" failed: %(emsg)s') % {
                    'dir': homedir, 'emsg': e }

        max_size = settings.USER_AVATAR_MAXSIZE
        avatar_name = settings.USER_AVATAR_NAME

        for f in self.request.files['avatar']:

            if len(f['body']) > max_size:
                return _('File should be less than %s') % human_size(max_size)

            tf = tempfile.NamedTemporaryFile()
            tf.write(f['body'])
            tf.seek(0)

            try:
                img = Image.open( tf.name )

            except Exception, e:
                return _('Open %(filename)s failed: %(emsg)s , is it a picture ?') % {
                    'filename': f.get('filename'), 'emsg': e }

            try:
                img.save(self.current_user.avatar_orig_path)
                img.thumbnail(settings.USER_AVATAR_THUM_SIZE, resample=1)
                img.save(self.current_user.avatar_path)
                img.thumbnail(settings.USER_AVATAR_MINI_THUM_SIZE, resample=1)
                img.save(self.current_user.avatar_mini_path)
                tf.close()

            except Exception, e:
                return _('Save %(filename)s failed: %(emsg)s') % {
                    'filename': f.get('filename'), 'emsg': e }



class PublicKeyIndex(RequestHandler):

    @authenticated
    def get(self):
        self.render('account/public_key/index.html')


class PublicKeyAdd(RequestHandler):

    title = _('Add Public Key')
    template_path = 'account/public_key/edit.html'

    @authenticated
    def prepare(self):

        self.form = PublicKeyForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form

        if form.validate():

            key = PublicKey( user = self.current_user,
                             name = form.name.data,
                             key = form.key.data )
            self.db.add( key )
            self.db.commit()

            if form.isdefault.data:
                key.set_default()
            self.db.commit()

            url = self.reverse_url('account:public_key')
            return self.redirect( url )

        self.render()



class PublicKeyHandler(RequestHandler):

    def initialize(self):

        self.key = None

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _("Give me the pulic key id please.") )

        key = self.db.query(PublicKey).get( ID )
        if not key:
            return self.write( _('Can not find public key %s') % ID )

        if key.user_id != self.current_user.id:
            return self.write( _('Not you public key.') )

        self.key = key
        self.prepare_kwargs['key'] = key



class PublicKeyEdit(PublicKeyHandler):

    title = _('Add Public Key')
    template_path = 'account/public_key/edit.html'

    @authenticated
    def prepare(self):

        if not self.key:
            return self.finish()

        self.form = PublicKeyForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.form.name.data = self.key.name
        self.form.key.data = self.key.data
        self.render()


    def post(self):

        form = self.form

        if form.validate():

            conflict = False

            for K in  self.db.query(PublicKey).filter_by(
                data = form.key.data ):
                if K.id == self.key.id: continue
                if K.data == form.key.data:
                    conflict = True

            if conflict:
                form.key.errors.append( _('This key is exist.') )

            else:
                self.key.name = form.name.data
                self.key.data = form.key.data

                if form.isdefault.data:
                    self.key.set_default()

                self.db.commit()

                url = self.reverse_url('account:public_key')
                return self.redirect( url )

        self.render()



class PublicKeyDelete(PublicKeyHandler):

    title = _('Add Public Key')
    template_path = 'account/public_key/edit.html'

    @authenticated
    def get(self):

        if not self.key:
            return self.finish()

        isdefault = self.key.isdefault

        self.db.delete( self.key )
        self.db.commit()

        if isdefault:
            for K in self.current_user.keys:
                K.isdefault = True
                break

            self.db.commit()

        url = self.reverse_url('account:public_key')
        self.redirect( url )


from tornado.auth import GoogleMixin
class GoogleHandler(RequestHandler, GoogleMixin):
    @asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")

        print 'user = ', user
        print 'type(user) = ', type(user)
        print 'dir(user) = ', dir(user)
        # Save the user with, e.g., set_secure_cookie()


from yweb.auth import QQAuth2Minix
class QQLogin(AccountRequestHandler, QQAuth2Minix):

    def prepare(self):

        Q = self.db.query(SiteConfig).filter_by(
            key = 'qq.auth2').first()

        if not Q:
            self.write( _('QQ Auth2 have not configured.') )
            return self.finish()

        QV = {}
        if Q and Q.value:
            QV = json.loads( Q.value )

        if not QV:
            self.write( _('QQ Auth2 have not configured.') )
            return self.finish()

        if not QV.get('enabled', False):
            self.write( _('QQ Auth2 login is disabled.') )
            return self.finish()

        self.client_id = QV.get('app_id', '')
        self.client_secret = QV.get('app_key', '')
        self.redirect_uri = QV.get('redirect_uri', '')

        if not ( self.client_id and self.client_secret and
                 self.redirect_uri ):
            self.write( _('QQ Auth2 configure has wrong.') )
            return self.finish()

        self.openid = None
        self.access_token = None


    @asynchronous
    def get(self):

        code = self.get_argument('code', None)

        if code:

            state1 = self.get_argument('state', None)
            state2 = self.get_secure_cookie('state_key')
            if state1 != state2:
                return self.write( _('state is not match.') )

            self.clear_cookie('state_key')

            self.get_authenticated_user(
                redirect_uri = self.redirect_uri,
                client_id = self.client_id,
                client_secret = self.client_secret,
                code = code,
                callback = self._on_auth )

        else:
            # first, set state string
            state = randstring(16)
            self.set_secure_cookie('state_key', state)

            self.authorize_redirect(
                redirect_uri = self.redirect_uri,
                client_id = self.client_id,
                extra_params = { 'state': state } )


    def _on_auth(self, session):
        if not session:
            raise tornado.web.HTTPError(500, "QQ auth failed")

        openid = session.get('openid', None)
        if not openid:
            self.write( _('Have not get openid') )
            return self.finish()

        O = self.db.query(OpenID).filter_by(
            openid = openid ).first()

        # user exist ?
        if O:
            if O.user_id:
                self.save_session(O.user_id)
                O.user.last_login = datetime.datetime.now()
                self.db.commit()
                return self.redirect('/')

            else:
                # create auth key
                K = AuthKey( data = O.openid, seconds = 3600*24*7 )
                self.db.add( K )
                self.db.commit()

                d = { 'auth_key': K.auth_key, 'openid': O.id }
                return self.render('account/openid_success.html',**d)

        # new user
        self.openid = openid
        self.access_token = session.get('access_token', None)

        if not ( self.openid and self.access_token ):
            self.write( _('QQ auth failed') )
            return self.finish()

        self.qq_request(
            path = '/user/get_user_info',
            method = 'GET',
            open_id = self.openid,
            token = self.access_token,
            client_id = self.client_id,
            callback = self._on_user_info )


    def _on_user_info(self, data):

        data = json.loads( data )

        ret = data.get('ret', None)
        if ret != 0:
            self.write(_('QQ auth failed: %s') % data.get('msg',''))
            return self.finish()

        # create openid
        O = OpenID( openid = self.openid, _type = 1 ) # TODO: QQ now
        O.config = json.dumps( { 'get_user_info': data } )
        self.db.add(O)
        self.db.commit()

        # create auth key
        K = AuthKey( data = O.openid, seconds = 3600 * 24 * 7 )
        self.db.add( K )
        self.db.commit()

        self.render('account/openid_success.html',
                    auth_key = K.auth_key, openid=O.id)


    def _on_user_info2(self, data):

        data = json.loads( data )

        ret = data.get('ret', None)
        if ret != 0:
            self.write(_('QQ auth failed: %s') % data.get('msg',''))
            return self.finish()

        # create new user
        O = OpenID( openid = self.openid, _type = 1 ) # TODO: QQ now
        O.config = json.dumps( { 'get_user_info': data } )
        self.db.add(O)
        self.db.commit()

        while True:
            username = 'QQ%s' % random.randint(1, 10000000)
            U = self.db.query(User).filter_by(username=username).first()
            if not U: break
            
        U = User( username = username,
                  password = 'not exist',
                  language = self.language )

        U.nickname = data.get('nickname', None)
        U.email_valid = True
        self.db.add( U )
        self.db.commit()

        U.init_account(self.db)

        self.save_session(U.id)
        U.last_login = datetime.datetime.now()

        O.user_id = U.id

        self.db.commit()

        # TODO: drop account relationships
        profile = UserProfile( U )
        self.db.add(profile)
        self.db.commit()

        self.redirect('/account')



class OpenIDHandler(AccountRequestHandler):

    def initialize(self):

        self.auth_key = None

        auth_key = self.get_argument('auth_key', None)

        if not auth_key:
            return self.write( _('No auth key') )

        K = self.db.query(AuthKey).filter_by(
            auth_key = auth_key).first()
        if not K:
            return self.write( _('Invalid key: %s') % auth_key )

        # TEST auth key data == openid.id
        openid = self.get_argument_int('openid', 0)
        if not openid:
            return self.write( _('No openid') )

        O = self.db.query(OpenID).get( openid )
        if not O:
            return self.write( _('Invalid openid %s') % openid )

        if K.auth_data != O.openid:
            return self.write( _('auth key and openid not match.') )

        self.auth_key = auth_key
        self.openid = O
        self.prepare_kwargs['auth_key'] = auth_key
        self.K = K


    @property
    def get_user_info(self):
        if not self.openid:
            return {}

        d = json.loads( self.openid.config )
        return d.get('get_user_info', {})



class OpenIDUserNew(OpenIDHandler):

    title = _('Create New User For OpenID')
    template_path = 'account/openid_user_new.html'

    def prepare(self):

        if not self.auth_key:
            return self.finish()

        self.form = OpenIDNewForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form
        openid = self.openid

        if form.validate():

            encpass = enc_login_passwd(form.password.data)
            U = User( username = form.username.data,
                      password = encpass,
                      language = self.language )

            user_info = self.get_user_info
            U.nickname = user_info.get('nickname', U.username)

            U.email = form.email.data

            self.db.add( U )
            self.db.commit()

            U.init_account(self.db)
            U.last_login = datetime.datetime.now()
            openid.user_id = U.id
            self.db.commit()

            self.save_session(U.id)
            self.db.delete(self.K)
            self.db.commit()

            return self.redirect_next('/account')

        self.render()



class OpenIDUserBinding(OpenIDHandler):

    title = _('Bingding My Account To OpenID')
    template_path = 'account/openid_user_binding.html'

    def prepare(self):

        if not self.auth_key:
            return self.finish()

        self.form = LoginForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form
        openid = self.openid

        if form.validate():

            U = form.true_user
            openid.user_id = U.id
            if not U.nickname or U.nickname == U.username:
                user_info = self.get_user_info
                U.nickname = user_info.get('nickname', U.username)

            self.save_session(U.id)

            self.db.delete(self.K)
            self.db.commit()

            return self.redirect_next('/')

        self.render()



class EmailValidate(RequestHandler):

    title = _('Validate My Email')
    template_path = 'account/email_validate.html'

    @authenticated
    def prepare(self):

        self.auth_key = self.get_argument('auth_key', None)

        form = EmailValidateForm(self)
        self.prepare_kwargs['form'] = form


    def get(self):

        if not self.auth_key:
            form = self.prepare_kwargs['form']
            form.email.data = self.current_user.email
            return self.render()

        K = self.db.query(AuthKey).filter_by(
            auth_key = self.auth_key).first()
        if not K:
            return self.write( _('Invalid key: %s') % self.auth_key )

        # Does expired ?
        if K.expire_date < datetime.datetime.now():
            return self.write( _('The key is expired: %s') % K.auth_key )

        self.current_user.email = K.auth_data
        self.current_user.email_valid = True
        self.db.delete( K )
        self.db.commit()

        self.redirect( self.reverse_url('account') )


    def post(self):

        form = self.prepare_kwargs['form']

        if form.validate():

            email = form.email.data

            U = self.db.query(User).filter(
                and_( User.id != self.current_user.id,
                      User.email == email )).first()

            if U:
                form.email.errors.append(
                    _('This email was used by other people.') )

            elif ( self.current_user.email == email and
                   self.current_user.email_valid ):
                form.email.errors.append(
                    _('This email was validate already.') )

            else:
                K = AuthKey( data = form.email.data,
                             seconds = 3600 * 24 * 7 )
                self.db.add( K )
                self.db.commit()

                # email
                self.mail_notice(email, K)
                return self.render('account/email_validate_apply_success.html')

        self.render()


    def mail_notice(self, email, K):

        host = SiteConfig.get(
            self.db, 'site.host', 'http://127.0.0.1')

        adr_from = SiteConfig.get(self.db, 'notice.smtp.fromaddr',
                                  'localhost@localhost')

        subject = _('[ LuoYunCloud ] Validate your email address.')

        validate_url = host + self.reverse_url('account:email:validate')
        validate_url += "?auth_key=%s" % K.auth_key

        d = { 'return_string': True,
              'validate_url': validate_url }

        body = self.render('account/email_validate_notice.html', **d)

        e = Email( subject = subject, text = body,
                   adr_to = email,
                   adr_from = adr_from,
                   mime_type = 'html' )
        self.quemail.send( e )
