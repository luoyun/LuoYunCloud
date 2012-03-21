# coding: utf-8

import os, base64, pickle, logging, struct, socket, re
import gettext
from hashlib import md5, sha512, sha1
import settings
import mako
import tornado

from mako.template import Template
from mako.lookup import TemplateLookup
mako.runtime.UNDEFINED = ''

from mako.exceptions import TemplateLookupException

from tornado.web import RequestHandler

template_dir = os.path.join(
    os.path.dirname(__file__), 'template' )


def fulltime(t):

    if t:
        return t.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return ''


class LyRequestHandler(RequestHandler):

    lookup = TemplateLookup([ template_dir ])

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
            reverse_url=self.application.reverse_url,

            LANGUAGES=self.settings['LANGUAGES'],
            STATIC_URL=self.settings['STATIC_URL'],
            THEME_URL=self.settings['THEME_URL'],

            #method
            fulltime = fulltime,
            has_permission = self.has_permission,
        )

        args.update(kwargs)

        # We can define keyword in views with initialize()
        if hasattr(self, 'view_kwargs'):
            args.update(self.view_kwargs)

        html = t.render(**args)
        self.finish(html)

    def get_current_user(self):
        """Override to determine the current user from, e.g., a cookie."""
        session_key = self.get_secure_cookie('session_key')
        if not session_key:
            return None

        session = self.db.get(
            'SELECT session_data FROM \
auth_session WHERE session_key=%s;',
            session_key )

        if not session:
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

        user_id = session_dict.get('user_id', None)
        if not user_id:
            return None

        user = self.db.get(
            "SELECT id, username, \
to_char(last_login, 'yyyy-MM-dd HH24:MI:SS') AS last_login, \
to_char(date_joined, 'yyyy-MM-dd HH24:MI:SS') AS date_joined \
FROM auth_user WHERE id = %s;",
            user_id )

        if not user:
            return None

        user.prefs = self.db.get(
            'SELECT * from user_profile WHERE user_id = %s;',
            user.id )

        return user

    def get_user_locale(self):
        user_locale = self.get_cookie("user_locale")

        if ( not user_locale and
             self.current_user and
             self.current_user.prefs and
             "locale" in self.current_user.prefs ):
            user_locale = self.current_user.prefs["locale"]

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

        user_perms = self.db.query(
            'SELECT * from user_permissions WHERE user_id=%s;',
            user.id)

        for up in user_perms:
            p = self.db.get(
                'SELECT * from auth_permission WHERE id=%s;',
                up.permission_id )
            if p and p.codename == perm:
                return True
                
        return False

    @property
    def db(self):
        return self.application.db

    def _job_notify(self, id):
        ''' Notify the new job signal to control server '''

        rqhead = struct.pack('iii', settings.PKT_TYPE_WEB_NEW_JOB_REQUEST, 4, id)

        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sk.connect( ( self.application.settings['control_server_ip'],
                      self.application.settings['control_server_port'] ) )

        sk.sendall(rqhead)
        sk.close()


    def new_job(self, target_type, target_id, action):

        SQL = "INSERT INTO job \
(user_id, status, target_type, target_id, action, created, started) \
VALUES (%s, %s, %s, %s, %s, 'now', 'now') RETURNING id;" % (
self.current_user.id, settings.JOB_S_INITIATED, target_type, target_id, action)
        try:
            r = self.db.query(SQL)
            #print 'new job id = ', r[0].id
            jid = r[0].id
            self._job_notify(jid)
            return jid

        except Exception, emsg:
            logging.error('Add new job to DB error: %s' % emsg)


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


    def appliance_logo_url(self, logoname):

        return '%s%s' % (
            self.settings['appliance_top_url'], logoname )

    def instance_logo_url(self, logoname):

        p = os.path.join(
            self.settings['static_path'],
            'instance_logo/%s' % logoname )

        if not os.path.exists(p):
            logoname = 'default.png'

        return '%s%s' % (
            '/static/instance_logo/', logoname )


    def job_status(self, code):
        # TODO: have a lazy translation

        JOB_STATUS_STR = {
            0: _('UNKNOWN'),
            100: _('INITIATED'),

            # mid-state of LY_A_NODE_RUN_INSTANCE

            200: _('Running'),
            201: _('Searching for Node Server'),
            202: _('Sending job to Node Server'),
            210: _('Waiting for resource available on Node Server'),
            211: _('Downloading Appliance image'),
            212: _('Checking Appliance image'),
            213: _('Creating Instance Disk File'),
            214: _('Mounting Instance Disk File'),
            215: _('Configuring Instance'),
            216: _('Un-Mounting Instance Disk File'),
            221: _('Starting Instance Virtual Machine'),
            250: _('Stopping Instance Virtual Machine'),
            299: _('Last Running Status'),

            # end of mid-state of LY_A_NODE_RUN_INSTANCE

            300: _('FINISHED'),
            301: _('FINISHED_SUCCESS'),
            302: _('FINISHED_INSTANCE_RUNNING'),
            303: _('FINISHED_INSTANCE_NOT_RUNNING'),
            304: _('FINISHED_INSTANCE_NOT_EXIST'),
            311: _('FINISHED_FAILURE'),
            321: _('FINISHED_FAILURE_NODE_NOT_AVAIL'),
            322: _('FINISHED_FAILURE_NODE_BUSY'),
            331: _('FINISHED_FAILURE_APP_NOT_AVAIL'),
            332: _('FINISHED_FAILURE_APP_ERROR'),
            399: _('FINISHED_LAST_STATUS'),

            # waiting for osmanager/application to start

            400: _('WAITING'),
            411: _('WAITING_STARTING_OSM'),
            412: _('WAITING_SYCING_OSM'),
            421: _('WAITING_STARTING_SERVICE'),
            499: _('WAITING_LAST_STATUS'),

            # job is pending
            500: _('PENDING'),

            # job is timed out
            600: _('TIMEOUT'),

            700: _('CANCEL'),
            701: _('CANCEL_INTERNAL_ERROR'),
            702: _('CANCEL_ALREADY_EXIST'),
            703: _('CANCEL_TARGET_BUSY'),
            711: _('CANCEL_ACTION_REPLACED'),
            799: _('CANCEL_LAST_STATUS'),
            }

        return JOB_STATUS_STR.get( code, _('Unknown') )
        

    # TODO: have a lazy translation
    def instance_status(self, code):

        INSTANCE_STATUS_STR = {
            0: _('unknown'),
            1: _("new domain that hasn't run once"),
            2: _('stopped'),
            3: _('started by hypervisor'),
            4: _('osm connected'),
            5: _('application is running'),
            9: _('suspend'),
            245: _('needs queryed'),
            255: _('not exist'),
        }

        return INSTANCE_STATUS_STR.get( code, _('Unknown') )



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
  <a href="${ page_url(cur_page -1) }">${ prev_str }</a>
  % endif

  % for p in plist:
  % if p == cur_page:
  <span class="count current">${ p }</span>
  % elif p == notexist_page:
  <span>...</span>
  % else:
  <a href="${ page_url(p) }"><span class="count">${ p }</span></a>
  % endif
  % endfor

  % if cur_page < page_sum:
  <a href="${ page_url(cur_page + 1) }">${ next_str }</a>
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
              'prev_str': 'Prev',
              'next_str': 'Next',
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
        logging.info('response = %s' % response)
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
            dre = u'href="http://luoyun.ylinux.org/proxy?host=%s&uri=/\g<1>"' % self.host
        else:
            dre = u'href="http://luoyun.ylinux.org/proxy?host=%s&port=%s&uri=/\g<1>"' % (self.host, self.port)

        body = re.sub(sre, dre, body)

        # for js, css
        sre = u'src="/([^"]*)'
        if self.port == 80:
            dre = u'src="http://luoyun.ylinux.org/proxy?host=%s&uri=/\g<1>"' % self.host
        else:
            dre = u'src="http://luoyun.ylinux.org/proxy?host=%s&port=%s&uri=/\g<1>"' % (self.host, self.port)

        body = re.sub(sre, dre, body)

        # for url
        sre = u'url\(/([^"]*)\)'
        if self.port == 80:
            dre = u'url(http://luoyun.ylinux.org/proxy?host=%s&uri=/\g<1>)' % self.host
        else:
            dre = u'url(http://luoyun.ylinux.org/proxy?host=%s&port=%s&uri=/\g<1>)' % (self.host, self.port)

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
