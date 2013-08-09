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

    url( r'/admin/system/nginx/edit', system.NginxEdit,
         name='system:nginx:edit' ),

    url( r'/admin/system/qqauth2/edit', system.QQAuth2Edit,
         name='system:qqauth2:edit' ),

    url( r'/admin/system/protocol/edit', system.RegistrationProtocolEdit,
         name='system:protocol:edit' ),

    url( r'/admin/system/welcome/edit', system.WelcomeNewUserEdit,
         name='system:welcome:edit' ),

    url( r'/admin/system/trace', system.LyTraceManage, name='admin:system:trace' ),

]
