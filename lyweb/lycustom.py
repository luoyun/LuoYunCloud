# coding: utf-8

import os, base64, pickle, logging, struct, socket, re, datetime
import urllib, urlparse
import gettext
from hashlib import md5, sha512, sha1
import settings
import mako
from mako.exceptions import RichTraceback
import tornado

from mako.template import Template
from mako.lookup import TemplateLookup
mako.runtime.UNDEFINED = ''

from mako.exceptions import TemplateLookupException

from tornado.web import RequestHandler
from tornado import escape

from app.account.models import User
from app.session.models import Session
from app.system.models import LyTrace

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from settings import JOB_ACTION, JOB_TARGET, LY_TARGET, TEMPLATE_DIR


from ytime import htime, ftime
from ytool.hstring import b2s


class LyRequestHandler(RequestHandler):

    lookup = TemplateLookup([ TEMPLATE_DIR ],
                            input_encoding="utf-8")

    def render(self, template_name, **kwargs):
        """ Redefine the render """

        t = self.lookup.get_template(template_name)

        args = dict(
            handler=self,
            request=self.request,
            current_user=self.current_user,
            locale=self.locale,
            _=self.locale.translate,
            static_url=self.static_url,
            xsrf_form_html=self.xsrf_form_html,
            xsrf_cookie=self.xsrf_cookie,
            reverse_url=self.application.reverse_url,

            LANGUAGES=self.settings['LANGUAGES'],
            STATIC_URL=self.settings['STATIC_URL'],
            THEME_URL=self.settings['THEME_URL'],
            THEME=self.settings['THEME'],
            theme_url=self.theme_url,

            #method
            htime = htime,
            ftime = ftime,
            has_permission = self.has_permission,
            show_error = show_error,
            b2s = b2s,
        )

        args.update(kwargs)

        # We can define keyword in views with initialize()
        if hasattr(self, 'view_kwargs'):
            args.update(self.view_kwargs)

        # TODO: more readable bug track
        # http://docs.makotemplates.org/en/latest/usage.html#handling-exceptions
        try:
            html = t.render(**args)
        except:
            traceback = RichTraceback()
            html = u'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <link rel="stylesheet" href="/static/css/mako.css" />
    <title>LuoYun Mako Template System Trac Info</title>
  </head>
  <body>
    <h1>LuoYun Mako Template System Trac Info</h1>
    <pre>'''
            for (filename, lineno, function, line) in traceback.traceback:
                html += "File %s, line %s, in %s" % (filename, lineno, function)
                html += "%s\n" % line
            html += "%s: %s" % (str(traceback.error.__class__.__name__), traceback.error)
            html += "</pre></body></html>"
        self.finish(html)


    def get_current_user(self):

        try:
            session = self.db2.query(Session).filter_by(
                session_key = self.get_secure_cookie('session_key')).one()
        except MultipleResultsFound:
            logging.error( 'session: MultipleResultsFound, %s' %
                           self.get_secure_cookie('session_key') )
        except NoResultFound:
            return None

        # Does session expired ?
        if session.expire_date < datetime.datetime.now():
            return None

        sk = self.settings["session_secret"]
        encoded_data = base64.decodestring(session.session_data)
        pickled, tamper_check = encoded_data[:-32], encoded_data[-32:]
        if md5(pickled + sk).hexdigest() != tamper_check:
            # TODO
            print "User tampered with session cookie."
            return None
        try:
            session_dict = pickle.loads(pickled)
        except:
            session_dict = {}

        user = self.db2.query(User).get(
            session_dict.get('user_id', 0) )

        if user:
            if user.islocked: return None

            user.last_active = datetime.datetime.now()
            user.last_entry = self.request.uri
            #self.db2.commit()

        return user


    def get_user_locale(self):
        user_locale = self.get_cookie("user_locale")

        if ( not user_locale and
             self.current_user and
             self.current_user.profile ):
            user_locale = self.current_user.profile.locale

        if user_locale:
            return tornado.locale.get(user_locale)
        else:
            # Use the Accept-Language header
            return None

    def has_permission(self, perm, user=None):

        if not user:
            user = self.current_user

        if not user:
            return False

        for p in self.current_user.permissions:
            if p.codename == perm or p.codename == 'admin':
                return True

        for g in self.current_user.groups:
            for p in g.permissions:
                if p.codename == perm or p.codename == 'admin':
                    return True

        return False


    @property
    def db(self):
        return self.application.db

    @property
    def db2(self):
        return self.application.db2

    def _job_notify(self, id):
        ''' Notify the new job signal to control server '''

        rqhead = struct.pack('iii', settings.PKT_TYPE_WEB_NEW_JOB_REQUEST, 4, id)

        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sk.connect( ( self.application.settings['control_server_ip'],
                      self.application.settings['control_server_port'] ) )

        sk.sendall(rqhead)
        sk.close()

    def _job_notify_new(self, ID):
        ''' Notify the new job signal to control server '''

        from settings import cf
        if cf.has_option('clc', 'clc_pass'):
            password = cf.get('clc', 'clc_pass')
        else:
            password = 'luoyun'

        d = {'from': 'web', 'to': 'clc', 'password': password, 'jobid': ID}
        self.application.clcstream.send_msg(d)

    def get_no_permission_url(self):
        self.require_setting("no_permission_url", "@has_permission")
        return self.application.settings["no_permission_url"]

    def get_no_resource_url(self):
        self.require_setting("no_resource_url")
        return self.application.settings["no_resource_url"]

    def theme_url(self, f):
        return self.static_url('themes/%s/%s' % (self.settings['THEME'], f))

    def get_int(self, value, default=0):
        try:
            return int(value)
        except:
            return default

    def get_argument_int(self, key, default=0):
        value = self.get_argument(key, default)
        try:
            return int(value)
        except:
            return default

    def lytrace(self, ttype, tid, do, isok=True, result=None):
        ip = self.request.remote_ip
        agent = self.request.headers.get('User-Agent')
        visit = self.request.uri

        T = LyTrace(self.current_user, ip, agent, visit)

        T.target_type = ttype,
        T.target_id = tid,
        T.do = do
        T.isok = isok
        T.result = result

        self.db2.add(T)
        self.db2.commit()

        return T

    # params is a dict: { 'key': value }
    def urlupdate(self, params):

        droped = [ k for k in params if params[k] == 'dropthis' ]
        for k in droped:
            del params[k]

        new = []

        if '?' in self.request.uri:
            path, oldparams = self.request.uri.split('?')
            update_keys = params.keys()

            for k, v in urlparse.parse_qsl( oldparams ):
                if k in droped: continue
                if k in update_keys:
                    v = params[k]
                    del params[k]
                new.append( (k, v) )
        else:
            path = self.request.uri

        if params:
            for k in params.keys():
                if k not in droped:
                    new.append( (k, params[k]) )

        return '?'.join([path, urllib.urlencode( new )])


    def xsrf_isok(self):
        token = (self.get_argument("_xsrf", None) or
                 self.request.headers.get("X-Xsrftoken") or
                 self.request.headers.get("X-Csrftoken"))
        if not token:
            return _("'_xsrf' argument missing")
        if self.xsrf_token != token:
            return _("XSRF cookie does not match")

    @property
    def xsrf_cookie(self):
        return escape.xhtml_escape(self.xsrf_token)

    def trans(self, s):
        return self.locale.translate(s)

    def msg2clc(self, key, msg, callback=None):
        ''' send a message to clc '''

        if not self.application.clcstream:
            return None, self.trans( _('No clc found !') )

        if not isinstance(msg, dict):
            return None, self.trans( _('Message must be a dict') )

        if callback:
            # must add callback handler
            msg['callback_id'] = self.application.get_unique_id()

        self.application.clcstream.send_msg(key, msg)



def show_error( E ):

    ''' return the error msg in list E '''

    return '<ul class="yerror">%s</ul>' % ''.join(['<li>%s</li>' % str(e) for e in E]) if E else ''



import functools, urlparse, urllib
def has_permission(codename):
    """ Needed permission 'codename'. """
    def foo(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.current_user:
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                            url += "?" + urllib.urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                raise HTTPError(403)

            # User is authenticated
            for p in self.current_user.permissions:
                if p.codename == codename or p.codename == 'admin':
                    return method(self, *args, **kwargs)

            for g in self.current_user.groups:
                for p in g.permissions:
                    if p.codename == codename or p.codename == 'admin':
                        return method(self, *args, **kwargs)

            #raise HTTPError(403, 'Need permission "%s"', codename)
            url = self.get_no_permission_url()
            url += "?codenames=%s" % codename
            return self.redirect( url )

        return wrapper
    return foo



class LyNotFoundHandler(LyRequestHandler):
    def prepare(self):
        try:
            self.set_status(404)
            self.render("/404.html")
        except TemplateLookupException, e:
            self.send_error(500)

