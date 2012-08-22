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

    url(r'/admin/system/networkpool', system.NetworkPool,
        name='system:networkpool'),
    url( r'/admin/system/networkpool/edit', system.NetworkPoolEdit,
         name='system:networkpool:edit' ),

    url( r'/admin/system/domain/edit', system.DomainEdit,
         name='system:domain:edit' ),

    url( r'/admin/system/nginx/edit', system.NginxEdit,
         name='system:nginx:edit' ),

    url( r'/admin/system/protocol/edit', system.RegistrationProtocolEdit,
         name='system:protocol:edit' ),

]
