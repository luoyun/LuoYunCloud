from tornado.web import url
import app.instance.views as instance

handlers = [

    url(r'/instance', instance.Index, name='instance'),

    # Instance
    url(r'/myun/instance/create', instance.CreateInstance, name='instance:create'),

    url(r'/instance/([0-9]+)', instance.View, name='instance:view'),

    url(r'/instance/([0-9]+)/control', instance.InstanceControl, name='instance:control'),
    
    (r'/instance/([0-9]+)/delete', instance.Delete),

    url(r'/instance/([0-9]+)/set_private',
        instance.SetPrivate, name='instance:set_private'),

    url(r'/instance/([0-9]+)/status', instance.Status, name='instance:status'),

    url(r'/instance/status', instance.CheckInstanceStatus, name='instance:status2'),

    url(r'/instance/single_status', instance.SingleInstanceStatus, name='instance:single_status'),

    url(r'/instance/([0-9]+)/islocked', instance.islockedToggle,
        name='instance:islocked'),

    url(r'/instance/([0-9]+)/isprivate', instance.isprivateToggle,
        name='instance:isprivate'),

    url(r'/instance/([0-9]+)/toggle_flag', instance.ToggleFlag, name='instance:toggle_flag'),

]
