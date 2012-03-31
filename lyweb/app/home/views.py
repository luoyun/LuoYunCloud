# coding: utf-8

import os

from lycustom import LyRequestHandler, Pagination
from tornado.web import authenticated




class Index(LyRequestHandler):

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


        inst_total = self.db.query(
            'SELECT id, cpus, memory, status FROM instance;' )
        TOTAL_INSTANCE = len( inst_total )
        TOTAL_APPLIANCE = len( self.db.query(
                'SELECT id FROM appliance;') )

        page_html = Pagination(
            total = TOTAL_INSTANCE,
            page_size = page_size,
            cur_page = cur_page ).html(self.get_page_url)


        # CPUS and Memory
        nodes = self.db.query( 'SELECT cpus, memory \
FROM node WHERE isenable=true' )
        TOTAL_CPU = 0
        TOTAL_MEMORY = 0
        for n in nodes:
            TOTAL_CPU += n.cpus
            TOTAL_MEMORY += n.memory


        USED_CPU = 0
        USED_MEMORY = 0
        RUNNING_INSTANCE = 0
        for i in inst_total:
            if i.status in [4, 5]:
                USED_CPU += i.cpus
                RUNNING_INSTANCE += 1
                USED_MEMORY += i.memory * 1024

        d = { 'title': _('LuoYun Home'),
              'TOTAL_CPU': TOTAL_CPU,
              'TOTAL_MEMORY': TOTAL_MEMORY / 1024,
              'USED_CPU': USED_CPU,
              'USED_MEMORY': USED_MEMORY / 1024,
              'TOTAL_APPLIANCE': TOTAL_APPLIANCE,
              'TOTAL_INSTANCE': TOTAL_INSTANCE,
              'RUNNING_INSTANCE': RUNNING_INSTANCE,
              'INSTANCE_LIST': instances,
              'cur_page': cur_page,
              'page_html': page_html,
              'instance_status': self.instance_status,
              'instance_logo_url': self.instance_logo_url }

        self.render("home/index.html", **d)



class SetLocale(LyRequestHandler):

    def get(self):

        user_locale = self.get_argument("language")
        next_url = self.get_argument("next", '/')
        self.set_cookie("user_locale", user_locale)

        self.redirect(next_url)
