from tornado.web import url
import app.system.views as system

handlers = [

    # System

    url(r'/admin/system', system.Index, name='system'),

    url(r'/admin/system/baseinfo/edit', system.BaseinfoEdit,
        name='system:baseinfo:edit'),

    url( r'/admin/system/db/edit', system.DBEdit,
         name='system:db:edit' ),

    url( r'/admin/system/clc/edit', system.CLCEdit,
         name='system:clc:edit' ),

    url( r'/admin/system/nameservers/edit', system.NameserversEdit,
         name='system:nameservers:edit' ),

    url(r'/system/ippool', system.IPPoolView, name='system:ippool'),
    url(r'/system/networkpool', system.NetworkHome,
        name='system:networkpool'),
    url(r'/system/networkpool/add', system.NetworkAdd,
        name='system:networkpool:add'),
    url(r'/system/networkpool/([0-9]+)', system.NetworkView,
        name='system:networkpool:view'),
    url(r'/system/networkpool/([0-9]+)/edit', system.NetworkEdit,
         name='system:networkpool:edit' ),
    url(r'/system/networkpool/([0-9]+)/delete', system.NetworkDelete,
         name='system:networkpool:delete' ),

    url( r'/admin/system/domain/edit', system.DomainEdit,
         name='system:domain:edit' ),

    url( r'/admin/system/nginx/edit', system.NginxEdit,
         name='system:nginx:edit' ),

    url( r'/admin/system/protocol/edit', system.RegistrationProtocolEdit,
         name='system:protocol:edit' ),

    url( r'/admin/system/welcome/edit', system.WelcomeNewUserEdit,
         name='system:welcome:edit' ),

    url( r'/admin/system/sendmail', system.SendMail,
         name='system:sendmail' ),

]
