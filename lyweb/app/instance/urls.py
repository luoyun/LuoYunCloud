from tornado.web import url
import app.instance.views as instance

handlers = [

    # Instance
    url(r'/instance/create', instance.CreateInstance, name='instance:create'),
    url(r'/instance/([0-9]+)', instance.View, name='instance:view'),

    (r'/instance/([0-9]+)/edit', instance.Edit),
    (r'/instance/([0-9]+)/delete', instance.Delete),
    (r'/instance/([0-9]+)/([a-z]+)', instance.Control),


]
