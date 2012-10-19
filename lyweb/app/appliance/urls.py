from tornado.web import url
import app.appliance.views as appliance

handlers = [

    url(r'/appliance', appliance.Index, name='appliance:index'),
    url(r'/appliance/upload', appliance.Upload, name='appliance:upload'),
    url(r'/appliance/([0-9]+)', appliance.View, name='appliance:view'),
    url(r'/appliance/([0-9]+)/edit', appliance.Edit, name='appliance:edit'),
    url(r'/appliance/([0-9]+)/delete', appliance.Delete, name='appliance:delete'),

    url(r'/appliance/([0-9]+)/set_useable', appliance.SetUseable,
        name='appliance:set_useable'),

    url(r'/appliance/([0-9]+)/set_private', appliance.SetPrivate,
        name='appliance:set_private'),

]
