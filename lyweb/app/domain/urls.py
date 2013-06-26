from tornado.web import url
from . import admin_views as admin
handlers = [

    url( r'/admin/domain', admin.DomainIndex,
         name='admin:domain' ),

    url( r'/admin/domain/edit', admin.DomainEdit,
         name='admin:domain:edit' ),

]
