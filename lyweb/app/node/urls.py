from tornado.web import url
import app.node.views as node

handlers = [

    # Job
    url(r'/node/([0-9]+)', node.Action, name='node:action'),

]
