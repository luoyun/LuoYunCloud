from tornado.web import url
import app.instance.views as instance

handlers = [

    url(r'/instance', instance.Index, name='instance'),

    # Instance
    url(r'/myun/instance/create', instance.CreateInstance, name='instance:create'),

    url(r'/instance/([0-9]+)', instance.View, name='instance:view'),
    url(r'/instance/([0-9]+)/baseinfo_edit', instance.BaseinfoEdit, name='instance:baseinfo:edit'),
    url(r'/instance/([0-9]+)/resource_edit', instance.ResourceEdit, name='instance:resource:edit'),
    url(r'/instance/([0-9]+)/network_edit', instance.NetworkEdit, name='instance:network:edit'),
    url(r'/instance/([0-9]+)/storage_edit', instance.StorageEdit, name='instance:storage:edit'),

    url(r'/instance/([0-9]+)/network_delete', instance.NetworkDelete, name='instance:network:delete'),
    url(r'/instance/([0-9]+)/storage_delete', instance.StorageDelete, name='instance:storage:delete'),

    url(r'/instance/([0-9]+)/password_edit', instance.PasswordEdit, name='instance:password:edit'),
    url(r'/instance/([0-9]+)/publickey_edit', instance.PublicKeyEdit, name='instance:publickey:edit'),

    url(r'/instance/([0-9]+)/domain_edit', instance.DomainEdit, name='instance:domain:edit'),
    url(r'/instance/([0-9]+)/domain_delete', instance.DomainDelete, name='instance:domain:delete'),

    url(r'/instance/([0-9]+)/webssh_enable', instance.WebSSHEnable, name='instance:webssh:enable'),
    url(r'/instance/([0-9]+)/webssh_disable', instance.WebSSHDisable, name='instance:webssh:disable'),

    (r'/instance/([0-9]+)/run', instance.Run),
    (r'/instance/([0-9]+)/stop', instance.Stop),
    (r'/instance/([0-9]+)/query', instance.Query),
    
    (r'/instance/([0-9]+)/delete', instance.Delete),

    url(r'/instance/([0-9]+)/set_private',
        instance.SetPrivate, name='instance:set_private'),

]
