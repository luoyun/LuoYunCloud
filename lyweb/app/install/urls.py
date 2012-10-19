from tornado.web import url
import app.install.views as install

handlers = [

    # System

    url(r'/install', install.Index, name='install'),
    url(r'/reload', install.Reload, name='reload'),

    url(r'/.*', install.Index),

]
