from tornado.web import url
from . import views
from . import admin_views

handlers = [
    url( r'/register', views.Register, name='register'),

    # admin
    url( r'/admin/registration', admin_views.Index,
         name='admin:registration'),

    url( r'/admin/registration/status_toggle',
         admin_views.RegistrationStatusToggle,
         name='admin:registration:status_toggle'),
]
