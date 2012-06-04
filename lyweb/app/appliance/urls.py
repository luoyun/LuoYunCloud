from tornado.web import url
import app.appliance.views as appliance

handlers = [

    url(r'/appliance', appliance.Index, name='appliance:index'),
    url(r'/appliance/upload', appliance.Upload, name='appliance:upload'),
    url(r'/appliance/([0-9]+)', appliance.View, name='appliance:view'),
    url(r'/appliance/([0-9]+)/edit', appliance.Edit, name='appliance:edit'),
    url(r'/appliance/([0-9]+)/delete', appliance.Delete, name='appliance:delete'),
    url(r'/appliance/([0-9]+)/create_instance', appliance.CreateInstance, name='appliance:create_instance'),

#    # Application
#    (r'/appliance', appliance.Index),
#    (r'/appliance/upload', appliance.Upload),
#    (r'/appliance/([0-9]+)', appliance.View),
#    (r'/appliance/([0-9]+)/edit', appliance.Edit),
#    (r'/appliance/([0-9]+)/delete', appliance.Delete),
#    (r'/appliance/([0-9]+)/create_instance', appliance.CreateInstance),
#
#    #(r'/appliance/add_catalog', appliance.AddCatalog),

]
