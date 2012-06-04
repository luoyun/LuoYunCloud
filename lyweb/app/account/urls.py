from tornado.web import url
import app.account.views as account

handlers = [
    url(r'/login', account.Login, name='login'),
    url(r'/logout', account.Logout, name='logout'),
    url(r'/register', account.Register, name='register'),
    url(r'/register_apply', account.RegisterApply, name='register_apply'),
    url(r'/account', account.Index, name='account:index'),

    url(r'/user/([0-9]+)', account.ViewUser, name='account:view'),
    url(r'/reset_password', account.ResetPassword, name='account:reset_password'),

]
