from tornado.web import url
from . import admin_views

handlers = [

    url(r'/admin/resource', admin_views.ResourceIndex,
        name='admin:resource'),

    url(r'/admin/resource/view', admin_views.ResourceView,
        name='admin:resource:view'),

    url(r'/admin/resource/edit', admin_views.ResourceEdit,
        name='admin:resource:edit'),

    url(r'/admin/resource/delete', admin_views.ResourceDelete,
        name='admin:resource:delete'),

]
