# coding: utf-8

import os, base64, pickle
from hashlib import md5, sha512, sha1
import settings
import mako
import tornado

from mako.template import Template
from mako.lookup import TemplateLookup
mako.runtime.UNDEFINED = ''

from mako.exceptions import TemplateLookupException

from tornado.web import RequestHandler


def fulltime(t):

    if t:
        return t.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return ''


class LyRequestHandler(RequestHandler):

    lookup = TemplateLookup(["./template"])
    #lookup = TemplateLookup(
    #    directories = ["./template"],
    #    default_filters = ['unicode', 'human_time'],
    #    imports = ['from lycustom import human_time'])

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

            LANGUAGES=settings.LANGUAGES,
            STATIC_URL=settings.STATIC_URL,
            THEME_URL=settings.THEME_URL,
            APPLIANCE_TOP_URL=self.application.settings["appliance_top_url"],

            #method
            fulltime = fulltime,
            has_permission = self.has_permission,
        )

        args.update(kwargs)

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

        sk = self.application.settings["session_secret"]
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



class LyNotFoundHandler(LyRequestHandler):
    def prepare(self):
        try:
            self.set_status(404)
            self.render("/404.html")
        except TemplateLookupException, e:
            self.send_error(500)



#def human_time(d):
#    print d
#    return d
