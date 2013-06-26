# coding: utf-8

from lycustom import RequestHandler

from app.auth.models import User

class View(RequestHandler):

    def get(self):

        ID = self.get_argument_int('id', 0)
        user = self.db.query(User).get(ID)
        if not user:
            return self.write( _('No such user: %s') % ID )

        self.render('account/user/view.html', user = user)
