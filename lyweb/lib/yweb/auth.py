#!/usr/bin/env python
#-*-coding: utf-8 -*-
from tornado import httpclient
from tornado import escape
from tornado.httputil import url_concat
from tornado.auth import OAuth2Mixin
from tornado import ioloop
from tornado import web
from tornado import gen
import logging
import re
import urllib


class QQAuth2Minix(OAuth2Mixin):

    _OAUTH_OPEND_API = "https://graph.qq.com"
    _OAUTH_AUTHORIZE_URL = "https://graph.qq.com/oauth2.0/authorize"
    _OAUTH_ACCESS_TOKEN_URL = "https://graph.qq.com/oauth2.0/token"
    _OAUTH_OPEND_ID_URL = "https://graph.qq.com/oauth2.0/me"
    _OAUTH_NO_CALLBACKS = False

    def authorize_redirect(self, redirect_uri=None, client_id=None,
                           client_secret=None, extra_params=None ):

        ''' fetch access_token

        e.g.

        fetch: 'https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=100467842&redirect_uri=http://www.LuoYunCloud.com'
        redirect: http://www.luoyuncloud.com/?code=4C0D2B833C3AC50AEC695D0C45A8D5CB
        '''

        args = {
            "response_type" : "code",
            "state": 'tets',
        }


        if extra_params:
            args.update(extra_params)

        super(QQAuth2Minix, self).authorize_redirect(
            redirect_uri  = redirect_uri,
            client_id     = client_id, 
            client_secret = client_secret, 
            extra_params  = args )


    @gen.engine
    def get_authenticated_user(self, redirect_uri, client_id, client_secret,
                              code, callback, extra_fields=None):
        ''' get token, openid

        e.g.

        fetch: 'https://graph.qq.com/oauth2.0/me?access_token=15D61D52CBE24DBAC66425FD91BCF046'
        ==>    'callback( {"client_id":"100467842","openid":"70B0270BD562F48D3415291370FB9569"} );'
        '''

        http = self.get_auth_http_client()
        args = {
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "extra_params": {
                "grant_type": "authorization_code"
            }
        }
        response = yield gen.Task(http.fetch, self._oauth_request_token_url(**args))
        self._on_access_token(redirect_uri, client_id,
                              client_secret, callback, response)

    @gen.engine
    def _on_access_token(self, redirect_uri, client_id, client_secret,
                        callback, response):
        if response.error:
            logging.warn('QQ auth error: %s' % str(response))
            callback(None)
            return
        args = escape.parse_qs_bytes(escape.native_str(response.body))
        session = {
            "access_token": args["access_token"][-1],
            "expires": args.get("expires_in")[0]
        }
        http = self.get_auth_http_client()
        response = yield gen.Task(http.fetch, url_concat(self._OAUTH_OPEND_ID_URL, {"access_token":session["access_token"]}))
        self._on_open_id(redirect_uri, client_id,
                         client_secret, callback, session, response)

    def _on_open_id(self, redirect_uri, client_id, client_secret,
                        callback, session, response):
        if response.error:
            logging.warning('QQ get openId error: %s' % str(response))
            callback(None)
            return
        res_json = re.match(r".*?\((.*?)\)", escape.native_str(response.body)).group(1)
        args = escape.json_decode(res_json)
        session.update(args)
        callback(session)

    @gen.engine
    def qq_request(self, path, method, open_id, token, client_id, callback, **args):
        """call qq auth2 api"""

        params = {
            "access_token" : token,
            "oauth_consumer_key" : client_id,
            "openid" : open_id
        }
        params.update(args)
        url = self._OAUTH_OPEND_API + path
        http = self.get_auth_http_client()
        if "POST" == method:
            response = yield gen.Task(http.fetch , url, method = method, body=urllib.urlencode(params))
            self._on_qq_request(callback, response)
        else:
            url = url_concat(url, params)
            response = yield gen.Task(http.fetch, url)
            self._on_qq_request(callback, response)


    def _on_qq_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s", response.error,
                            response.request.url)
            callback(None)
            return
        callback(escape.native_str(response.body))


    def get_auth_http_client(self):
        """Returns the AsyncHTTPClient instance to be used for auth requests.

        May be overridden by subclasses to use an http client other than
        the default.
        """
        return httpclient.AsyncHTTPClient()
