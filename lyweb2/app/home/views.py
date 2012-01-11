# coding: utf-8

from lycustom import LyRequestHandler
from tornado.web import authenticated


class Index(LyRequestHandler):
    #@authenticated
    def get(self):
        jobs = self.db.query(
            "SELECT * from job ORDER BY ended LIMIT 3;;")

        for j in jobs:
            j.user = self.db.get(
                "SELECT * from auth_user WHERE id=%s;",
                j.user_id )

        users = self.db.query('SELECT * from auth_user;')

        d = { 'title': "LuoYun Home", 'jobs': jobs,
              'total_user': len(users) }
        self.render("home/index.html", **d)


class SetLocale(LyRequestHandler):
    def get(self):
        self.writing('Just for POST !')

    def post(self):
        user_locale = self.get_argument("language")
        self.set_cookie("user_locale", user_locale)
        self.redirect('/')


class Test(LyRequestHandler):

    def get(self):
        d = { 'title': 'TEST Title From LuoYun'}
        self.render("home/index.html", **d)

