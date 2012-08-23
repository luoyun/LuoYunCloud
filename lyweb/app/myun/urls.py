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

]
