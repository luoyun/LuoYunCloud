from tornado.web import url
import app.instance.views as I

handlers = [

    url(r'/instance', I.Index, name='instance'),

    url(r'/instance/view', I.View, name='instance:view'),

    url(r'/instance/single_status', I.SingleInstanceStatus,
        name='instance:single_status'),

    url(r'/instance/lifecontrol', I.LifeControl,
        name='instance:lifecontrol'),

    url(r'/instance/attr_set', I.AttrSet, name='instance:attr_set'),

    url(r'/instance/delete', I.InstanceDelete,
        name='instance:delete'),

]
