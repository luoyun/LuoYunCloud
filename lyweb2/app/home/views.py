# coding: utf-8

import os

from lycustom import LyRequestHandler, Pagination
from tornado.web import authenticated




class Index(LyRequestHandler):

    def initialize(self):
        
        self.view_kwargs = {
            'instance_logo_url': self.instance_logo_url }


    def get(self):

        by = self.get_argument('by', 'created')
        sort = self.get_argument('sort', 'DESC')
        page_size = int(self.get_argument('sepa', 10))
        cur_page = int(self.get_argument('p', 1))

        # TODO: no SQL-injection
        if not ( sort in ['DESC', 'ASC'] and
                 by  in ['updated', 'created'] ):
            return self.write(u'wrong URL !')

        offset = (cur_page - 1) * page_size

        SQL = "\
SELECT id, name, summary, logo, cpus, memory, user_id, \
       appliance_id, node_id, ip, status, created, updated \
FROM instance \
ORDER BY %s %s \
LIMIT %s OFFSET %s;" % (by, sort, page_size, offset)

        instances = self.db.query(SQL)

        for I in instances:
            I.user = self.db.get('SELECT id, username \
FROM auth_user WHERE id=%s;', I.user_id )


        TOTAL_INSTANCE = len( self.db.query(
                'SELECT id FROM instance;') )
        TOTAL_APPLIANCE = len( self.db.query(
                'SELECT id FROM appliance;') )

        page_html = Pagination(
            total = TOTAL_INSTANCE,
            page_size = page_size,
            cur_page = cur_page ).html(self.get_page_url)


        d = { 'title': _('LuoYun Home'),
              'TOTAL_APPLIANCE': TOTAL_APPLIANCE,
              'TOTAL_INSTANCE': TOTAL_INSTANCE,
              'INSTANCE_LIST': instances,
              'cur_page': cur_page,
              'page_html': page_html,
              'instance_status': self.instance_status }

        self.render("home/index.html", **d)


class SetLocale(LyRequestHandler):
    def get(self):
        self.write('Just for POST !')

    def post(self):
        user_locale = self.get_argument("language")
        self.set_cookie("user_locale", user_locale)
        self.redirect('/')




class Test(LyRequestHandler):

    def get(self):
        d = { 'title': 'TEST Title From LuoYun'}
        self.render("home/index.html", **d)

