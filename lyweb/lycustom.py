# coding: utf-8

import os, base64, pickle, logging, struct, socket, re, datetime
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

from app.account.models import User
from app.session.models import Session

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


template_dir = os.path.join(
    os.path.dirname(__file__), 'template' )


from dateutil import tz

from_zone = tz.gettz('UTC')  # UTC Zone
to_zone = tz.gettz('CST')    # China Zone

def lytime(t, f='%m-%d %H:%M', UTC=False):

    if t:
        if from_zone and to_zone and not UTC:
            utc = t.replace(tzinfo=from_zone)
            t = utc.astimezone(to_zone)

        return datetime.datetime.strftime(t, f)

    else:
        return ''


def fulltime(t, UTC=False):

    if t:
        if from_zone and to_zone and not UTC:
            utc = t.replace(tzinfo=from_zone)
            t = utc.astimezone(to_zone)

        return datetime.datetime.strftime(t, '%Y-%m-%d %H:%M:%S')

    else:
        return ''


from ytime import ytime_human

class LyRequestHandler(RequestHandler):

    lookup = TemplateLookup([ template_dir ],
                            input_encoding="utf-8")

    def render(self, template_name, **kwargs):
        """ Redefine the render """

        # TODO: if url have ajax arg, use XXX.ajax for template
        ajax = self.get_argument('ajax', False)
        if ajax:
            x, y = template_name.split('.')
            #x += '_ajax'
            template_name = '.'.join([x,'ajax'])

        t = self.lookup.get_template(template_name)

        args = dict(
            handler=self,
            request=self.request,
            current_user=self.current_user,
            locale=self.locale,
            _=self.locale.translate,
            static_url=self.static_url,
            xsrf_form_html=self.xsrf_form_html,
            reverse_url=self.application.reverse_url,

            LANGUAGES=self.settings['LANGUAGES'],
            STATIC_URL=self.settings['STATIC_URL'],
            THEME_URL=self.settings['THEME_URL'],
            THEME=self.settings['THEME'],
            theme_url=self.theme_url,

            #method
            fulltime = fulltime,
            ytime_human = ytime_human,
            lytime = lytime,
            has_permission = self.has_permission,
            AJAX = ajax,
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
        if session.expire_date < datetime.datetime.utcnow():
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

        if user.islocked: return None

        if user:
            user.last_active = datetime.datetime.utcnow()
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
            # TODO: app and template have different i18n
            gettext.translation(
                'app', settings.I18N_PATH,
                languages=[user_locale]).install(True)
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


    def get_page_url(self, p, path=None):

        ''' Generate page url from given p (cur_page)

        For Pagination.
        '''

        if not path:
            path = self.request.uri

        the_p = 'p=%s' % p

        if path.count('p='):
            return re.sub('p=[0-9]+', the_p, path)
        elif path.count('?'):
            return path + '&%s' % the_p
        else:
            return path + '?%s' % the_p


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


from mako.template import Template
class Pagination:

    ''' A pagination generator '''

    def __init__( self, total, page_size, cur_page,
                  list_size = 5 ):

        self.size = page_size

        self.sum = total / page_size
        if ( total % page_size ): self.sum += 1

        self.cur = cur_page
        self.lsize = list_size

        self.notexist_p = self.sum + 1

        self.HTML = u'''
<div class="pagination">

  % if cur_page > 1:
  <a href="${ page_url(cur_page -1) }"><span class="endside">${ prev_str }<span></a>
  % else:
  <span class="endside">${ prev_str }</span>
  % endif

  % for p in plist:
  % if p == cur_page:
  <span class="page current">${ p }</span>
  % elif p == notexist_page:
  <span>...</span>
  % else:
  <a href="${ page_url(p) }"><span class="page">${ p }</span></a>
  % endif
  % endfor

  % if cur_page < page_sum:
  <a href="${ page_url(cur_page + 1) }"><span class="endside">${ next_str }</span></a>
  % else:
  <span class="endside">${ next_str }</span>
  % endif

</div>
'''


    def _page_list(self):

        last_p = self.sum

        start = ( self.cur / (self.lsize + 1) ) * self.lsize + 1
        end = start + self.lsize
        if end > last_p: end = last_p

        plist = range(start, end + 1)

        if end < last_p:
            plist.extend( [self.notexist_p, last_p] )
        if self.cur > self.lsize:
            plist.insert(0, self.notexist_p)
            plist.insert(0, 1)

        return plist


    def html(self, page_url):

        if self.sum <=1:
            return ''

        d = { 'plist': self._page_list(),
              'prev_str': _('Prev'),
              'next_str': _('Next'),
              'cur_page': self.cur,
              'page_sum': self.sum,
              'page_url': page_url,
              'notexist_page': self.notexist_p }

        t = Template(self.HTML)
        return t.render(**d)




from tornado.web import asynchronous, HTTPError
from tornado import httpclient
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
class LyProxyHandler(LyRequestHandler):
    ''' Web Proxy '''

    def prepare(self):
        self.host = self.get_argument('host', '')
        self.port = int(self.get_argument('port', 80))
        self.uri = self.get_argument('uri', '/')

        if not self.host:
            self.write('No host found')
            self.finish()

    @asynchronous
    def get(self):

        if self.port == 80:
            url = 'http://%s%s' % (self.host, self.uri)
        else:
            url = 'http://%s:%s%s' % (self.host, self.port, self.uri)
        try:
            AsyncHTTPClient().fetch(url, self._on_proxy)
        except tornado.httpclient.HTTPError, x:
            if hasattr(x, "response") and x.response:
                self._on_proxy(x.response)
            else:
                logging.error("Tornado signalled HTTPError %s", x)
 
    def _on_proxy(self, response):
        #logging.info('response = %s' % response)
        if response.error and not isinstance(response.error,
                                             tornado.httpclient.HTTPError):
            raise HTTPError(500)
        else:
            self.set_status(response.code)
            for header in ("Date", "Cache-Control", "Server", "Content-Type", "Location"):
                v = response.headers.get(header)
                if v:
                    self.set_header(header, v)
            if response.body:
                # replace url
                body = self.replace_url(response.body)
                self.write(body)
            self.finish()

    def replace_url(self, body):

        # for link
        sre = u'href="/([^"]*)'
        if self.port == 80:
            dre = u'href="/proxy?host=%s&uri=/\g<1>"' % self.host
        else:
            dre = u'href="/proxy?host=%s&port=%s&uri=/\g<1>"' % (self.host, self.port)

        body = re.sub(sre, dre, body)

        # for js, css
        sre = u'src="/([^"]*)'
        if self.port == 80:
            dre = u'src="/proxy?host=%s&uri=/\g<1>"' % self.host
        else:
            dre = u'src="/proxy?host=%s&port=%s&uri=/\g<1>"' % (self.host, self.port)

        body = re.sub(sre, dre, body)

        # for url
        sre = u'url\(/([^"]*)\)'
        if self.port == 80:
            dre = u'url(/proxy?host=%s&uri=/\g<1>)' % self.host
        else:
            dre = u'url(/proxy?host=%s&port=%s&uri=/\g<1>)' % (self.host, self.port)

        body = re.sub(sre, dre, body)

        return body


    @asynchronous
    def post(self):
#        protocol = 'http'
#        host = 'luoyun.ylinux.org'
#        port = '80'
# 
#        # port suffix
#        port = "" if port == "80" else ":%s" % port
# 
#        uri = self.request.uri
#        url = "%s://%s%s%s" % (protocol, host, port, uri)

        if self.port == 80:
            url = 'http://%s%s' % (self.host, self.uri)
        else:
            url = 'http://%s:%s%s' % (self.host, self.port, self.uri)
 
        # update host to destination host
        headers = dict(self.request.headers)
        headers["Host"] = self.host
 
        try:
            AsyncHTTPClient().fetch(
                HTTPRequest(url=url,
                            method="POST",
                            body=self.request.body,
                            headers=headers,
                            follow_redirects=False),
                self._on_proxy2)
        except tornado.httpclient.HTTPError, x:
            if hasattr(x, "response") and x.response:
                self._on_proxy(x.response)
            else:
                logging.error("Tornado signalled HTTPError %s", x)
 
    def _on_proxy2(self, response):
        if response.error and not isinstance(response.error,
                                             tornado.httpclient.HTTPError):
            raise HTTPError(500)
        else:
            self.set_status(response.code)
            for header in ("Date", "Cache-Control", "Server", "Content-Type", "Location"):
                v = response.headers.get(header)
                if v:
                    self.set_header(header, v)
            if response.body:
                body = self.replace_url(response.body)
                self.write(body)
            self.finish()

