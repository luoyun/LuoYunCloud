# coding: utf-8

import os, logging, json, time

import datetime
import base64
import pickle
import random
from hashlib import sha1, md5

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from yweb.contrib.session.models import Session
from app.auth.models import User
from app.auth.utils import check_login_passwd

from app.instance.models import Instance

import settings

from lycustom import RequestHandler, has_permission


import functools
def authenticated(method):
    """ ref: tornado/web.py authenticated """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            return self.write_fail( _('Requires authentication') )
        return method(self, *args, **kwargs)
    return wrapper



class ApiRequestHandler(RequestHandler):


    def get_current_user(self):

        session_key = self.get_argument('session_key', None)

        try:
            session = self.db.query(Session).filter_by(
                session_key = session_key).one()
        except MultipleResultsFound:
            logging.error( 'session: MultipleResultsFound, %s' % session_key )
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

        user = self.db.query(User).get( session_dict.get('user_id', 0) )

        if user and user.is_locked:
            return None

        return user


    def check_xsrf_cookie(self):
        pass


    def write_success(self, desc, **kwargs):
        args = dict(code = 0, desc = desc)
        args.update(kwargs)

        self.write( args )


    def write_fail(self, desc, code=1, **kwargs):
        args = dict(code = code, desc = desc)
        args.update(kwargs)

        self.write( args )



class Login(ApiRequestHandler):


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

# TODO
        self.set_secure_cookie('session_key', session_key)

        return session_key


    def post(self):

        username = self.get_argument('username', None)
        password = self.get_argument('password', None)

        print 'self.request = ', self.request

        print 'username = ', username
        print 'password = ', password

        U = self.db.query(User).filter_by( username = username ).first()
        print 'U = ', U
        if not U:
            return self.write_fail( _('No such user.') )

        if U:
            if U.is_locked:
                return self.write_fail( _('User is locked') )

        if not check_login_passwd( password, U.password ):
            return self.write_fail( _('Password is wrong.') )

        session_key = self.save_session( U.id )

        U.last_login = datetime.datetime.now()

        self.db.commit()

        self.write_success( _('Welcome to LYC.'),
                            session_key = session_key )



class InstanceBaseinfo(ApiRequestHandler):

    @authenticated
    def post(self):

        ID = self.get_argument_int('instance_id', None)
        if not ID:
            return self.write_fail( _('Give me instance_id please.') )

        I = self.db.query(Instance).get( ID )
        if not I:
            return self.write_fail( _('Can not find instance %s') % ID )

        if I.user_id != self.current_user.id:
            return self.write_fail( _("Instance %s is someone else's") )

        d = { 'desc': 'Information about %s' % I.name,
              'instance_id': I.id,
              'vdi_type': 1,
              'host': I.node.ip,
              'port': I.vdi_port }

        self.write_success( **d )



class MyInstanceList(ApiRequestHandler):

    @authenticated
    def post(self):

        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        IL = self.db.query(Instance).filter_by(
            user_id = self.current_user.id )

        total = IL.count()

        if total:

            IL = IL.slice(start, stop).all()

            data = []
            for I in IL:
                data.append( {
                        'id': I.id,
                        'name': I.name,
                        'summary': I.summary,
                        'status': I.status,
                        'status_string': I.status_string,
                        })

            d = { 'desc': 'List %s instances' % len(IL),
                  'list': data }
            self.write_success( **d )

        else:
            self.write_fail( _('No instances found') )
