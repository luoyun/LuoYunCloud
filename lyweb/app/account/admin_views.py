# coding: utf-8

import logging
from lycustom import RequestHandler, has_permission
from app.auth.models import User
from app.site.models import SiteConfig
from tornado.web import asynchronous

from .forms import MailToForm


class MailTo(RequestHandler):

    ''' Send a mail to multi user '''

    title = _('Send Mail To User')
    template_path = 'admin/account/mailto.html'

    @has_permission('admin')
    def prepare(self):
        # id list
        _IDS = self.get_argument('user', '')
        ID_LIST = []

        for x in _IDS.split(','):
            x = x.strip()
            if x:
                ID_LIST.append(x)

        USER_LIST = []
        for ID in ID_LIST:
            U = self.db.query(User).get( ID )
            if U and U.email and U.email_valid:
                USER_LIST.append( U )

        self.USER_LIST = USER_LIST
        self.prepare_kwargs['USER_LIST'] = USER_LIST
        self.prepare_kwargs['form'] = MailToForm(self)

    def get(self):
        self.render()

    def post(self):

        form = self.prepare_kwargs['form']

        if form.validate():

            response = self.send_mail()

            url = self.reverse_url('admin:site:job')
            return self.redirect_next( url )

        self.render()


    def send_mail(self):

        form = self.prepare_kwargs['form']

        from markdown import Markdown
        YMK = Markdown(extensions=['fenced_code', 'tables'])

        body =  YMK.convert( form.body.data )

        USER_LIST = self.USER_LIST

        UID = [ U.id for U in USER_LIST ]

        response = self.sendmsg(
            uri = 'mailto.userlist',
            data = { 'uid': self.current_user.id,
                     'ID_LIST': UID,
                     'subject': form.subject.data,
                     'body': body } )
        return response
