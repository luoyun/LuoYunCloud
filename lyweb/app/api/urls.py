from tornado.web import url
from . import views

handlers = [

    ( r'/api/login', views.Login ),
    ( r'/api/instance/baseinfo', views.InstanceBaseinfo ),
    ( r'/api/myun/instance', views.MyInstanceList ),
]
