# coding: utf-8

from lycustom import LyRequestHandler

import random, time, pickle, base64
from hashlib import md5, sha512, sha1

import tornado
from tornado.web import authenticated, asynchronous



def encrypt_password(salt, raw_password):
    hsh = sha512(salt + raw_password).hexdigest()
    return hsh

def check_password(raw_password, enc_password):
    try:
        salt, hsh = enc_password.split('$')
    except:
        return False
    return hsh == encrypt_password(salt, raw_password)
    


class Login(LyRequestHandler):

    def get(self):

        self.render("account/login.html",
                    next_url = self.get_argument('next', '/'))

    def post(self):

        username = self.get_argument('username', '')
        password = self.get_argument('password', '')

        user = self.db.get(
            "SELECT * FROM auth_user WHERE username=%s;",
            username )

        d = { 'username': username, 'password': password,
              'user': user, 'ERROR': [],
              'next_url': self.get_argument('next', '/') }

        if user:
            if check_password(password, user.password):
                # login success, save a session
                self.save_session(user.id)
                #self.write("Have not completed ! d = %s" % d)
                print 'next_url = ', d['next_url']
                self.redirect( d['next_url'] )
            else:
                d['ERROR'].append( _('Password is wrong.') )
                self.render('account/login.html', **d)
        else:
            d['ERROR'].append( _('Have not found user.') )
            self.render('account/login.html', **d)

    def save_session(self, user_id):
        self.require_setting("cookie_secret", "secure cookies")

        session_key = sha1('%s%s' % (random.random(), time.time())).hexdigest()
        self.set_secure_cookie('session_key', session_key)

        session_dict = {'user_id': user_id}
        sk = self.application.settings["session_secret"]
        pickled = pickle.dumps(session_dict, pickle.HIGHEST_PROTOCOL)
        pickled_md5 = md5(pickled + sk).hexdigest()
        session_data = base64.encodestring(pickled + pickled_md5)

        self.db.execute(
            "INSERT INTO auth_session \
(session_key, session_data, expire_date) \
VALUES (%s, %s, now()::timestamp + '14 day');",
            session_key, session_data )





class Logout(LyRequestHandler):
    @authenticated
    def get(self):
        if self.current_user:
            self.delete_session(self.current_user.id)
            self.redirect('/')
        else:
            d['username_error'] = 'Have not found user.'
            self.render('account/login.html', **d)

    def delete_session(self, user_id):
        session_key = self.get_secure_cookie('session_key')
        self.db.execute(
            'DELETE FROM auth_session WHERE session_key = %s;',
            session_key )
        self.clear_all_cookies()


# TODO: No used now
class Register(LyRequestHandler):

    def get(self):
        self.render('account/register.html')

    def post(self):

        username = self.get_argument('username', '')
        password = self.get_argument('password', '')

        d = { 'username': username, 'ERROR': [] }

        user = self.db.get(
            'SELECT * from auth_user WHERE username=%s;',
            username )

        if user:
            d['ERROR'].append( _('This username is taked.') )
            return self.render('account/register.html', **d)

        if len(password) < 6:
            d['ERROR'].append( _('password must have more than 6 characters !') )
            return self.render('account/register.html', **d)

        salt = md5(str(random.random())).hexdigest()[:12]
        hsh = encrypt_password(salt, password)
        enc_password = "%s$%s" % (salt, hsh)
        try:
            # create user
            self.db.execute(
                "INSERT INTO auth_user (username, password, last_login, date_joined) VALUES (%s, %s, 'epoch', 'now');",
                username, enc_password )

            # query user
            user = self.db.get(
                'SELECT * from auth_user WHERE username=%s;',
                username )

            # create user profile
            self.db.execute(
                "INSERT INTO user_profile (user_id) VALUES (%s);",
                user.id )
            return self.redirect('/')

        except Exception, emsg:
            d['ERROR'].append( _('System error: %s') % emsg )
            self.render('account/register.html', **d)



class Create(LyRequestHandler):
    ''' Create a new account, by admin '''

    def initialize(self):

        self.t = 'account/create.html'

    @authenticated
    def prepare(self):
        if self.current_user.id not in [ 1 ]:
            self.write('No permissions !')
            return self.finish()


    def get(self):
        self.render(self.t)


    def post(self):

        username = self.get_argument('username', '')
        password = self.get_argument('password', '')

        d = { 'username': username, 'ERROR': [] }

        user = self.db.get(
            'SELECT * from auth_user WHERE username=%s;',
            username )

        if user:
            d['ERROR'].append( _('This username is taked.') )
            return self.render(self.t, **d)

        if len(password) < 6:
            d['ERROR'].append( _('password must have more than 6 characters !') )
            return self.render(self.t, **d)

        salt = md5(str(random.random())).hexdigest()[:12]
        hsh = encrypt_password(salt, password)
        enc_password = "%s$%s" % (salt, hsh)
        try:
            # create user
            r = self.db.query(
                "INSERT INTO auth_user (username, \
password, last_login, date_joined) VALUES (%s, %s, \
'epoch', 'now') RETURNING id;",
                username, enc_password )

            uid = r[0].id

            # create user profile
            self.db.execute( "INSERT INTO user_profile \
(user_id) VALUES (%s);", uid )

            return self.redirect( '/account/%s' % uid )

        except Exception, emsg:
            d['ERROR'].append( _('System error: %s') % emsg )
            self.render( self.t, **d )



class User(LyRequestHandler):

    @authenticated
    def get(self, id):

        user = self.db.get(
            'SELECT * from auth_user WHERE id=%s;', id )

        if not user:
            return self.write('Have not found user by id %s' % id)

        user.prefs = self.db.get(
            'SELECT * from user_profile WHERE user_id = %s;',
            user.id )

        INSTANCE_LIST = self.db.query(
            'SELECT id, name FROM instance WHERE user_id=%s',
            user.id )

        self.render( 'account/view_user.html',
                     title = 'View User', user = user,
                     INSTANCE_LIST = INSTANCE_LIST )



class Chat(LyRequestHandler):

    def get(self):
        d = { 'messages': [] }
        self.render('account/chat.html', **d)


class Online(LyRequestHandler):

    @asynchronous
    def post(self):

        total = int(self.get_argument("total", 0))


        self.is_total_changed(total, 0)

    def is_total_changed(self, total, num):

        num += 1;

        if self.request.connection.stream.closed():
            return

        users = self.db.query("SELECT * from auth_user;")

        print "[%s], total = %s, len(users) = %s" % (num, total, len(users))

        if len(users) == total:
            print "add_timeout"
            tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + 10, lambda: self.is_total_changed(total, num) )
        else:
            print "go finish"
            self.write(str(len(users)))
            self.finish()


class UserList(LyRequestHandler):

    def get(self):

        users = self.db.query('SELECT * from auth_user;')

        self.render( 'account/user_list.html',
                     title = 'User List',
                     users = users )


class ResetPassword(LyRequestHandler):

    def initialize(self):
        self.t = 'account/reset_password.html'

    @authenticated
    def get(self, id):

        emsg = self.check_permission(id)
        if emsg:
            return self.write(emsg)

        self.render( 'account/reset_password.html',
                     title = 'Reset Password',
                     user = self.user )

    @authenticated
    def post(self, id):

        emsg = self.check_permission(id)
        if emsg:
            return self.write(emsg)

        d = { 'title': 'Reset Password', 'ERROR': [] }

        password = self.get_argument('password', '')
        password2 = self.get_argument('password2', '')

        if len(password) < 6:
            d['ERROR'].append( _('password must have more than 6 characters !') )
            return self.render(self.t, **d)

        if password != password2:
            d['ERROR'].append( _('password now match') )
            return self.render(self.t, **d)

        salt = md5(str(random.random())).hexdigest()[:12]
        hsh = encrypt_password(salt, password)
        enc_password = "%s$%s" % (salt, hsh)

        try:
            self.db.execute( 'UPDATE auth_user \
SET password=%s WHERE id=%s;', enc_password, id )
        except Exception, emsg:
            d['ERROR'].append( _('UPDATE failed: %s') % emsg )
            return self.render('account/reset_password.html', **d)
        self.redirect('/account/%s' % id)


    def check_permission(self, id):
        
        if self.current_user.id not in [1, int(id)]:
            return 'Don not do this !'

        self.user = self.db.get(
            'SELECT * from auth_user WHERE id=%s;', id)

        if not self.user:
            return _('Have not found user %s') % id
        
        return None

