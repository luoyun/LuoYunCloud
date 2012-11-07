from tornado.web import url
import app.myun.views as myun

# TODO: Just a hack
import app.instance.views as instance

handlers = [

    url( r'/myun', myun.Index, name='myun:index'),

    url( r'/myun/instance', myun.MyunInstance,
         name='myun:instance'),

    url( r'/myun/appliance', myun.MyunAppliance,
         name='myun:appliance'),

    url( r'/myun/instance/([0-9]+)', myun.InstanceView,
         name='myun:instance:view'),

    url( r'/myun/instance/([0-9]+)/edit', myun.InstanceEdit,
         name='myun:instance:edit'),

]
