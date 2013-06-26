from tornado.web import url
import app.instance.views as instance

handlers = [

    url(r'/instance', instance.Index, name='instance'),

    url(r'/instance/view', instance.View, name='instance:view'),

    url(r'/instance/single_status', instance.SingleInstanceStatus, name='instance:single_status'),

    url(r'/instance/lifecontrol', instance.LifeControl, name='instance:lifecontrol'),

    url(r'/instance/attr_set', instance.AttrSet, name='instance:attr_set'),

]
