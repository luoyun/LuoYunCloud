from tornado.web import url

from . import admin_views as admin

handlers = [

    url(r'/admin/network', admin.Index, name='admin:network'),

    # Network Pool
    url(r'/admin/network/config', admin.NetworkConfig,
        name='admin:network:config'),

    url(r'/admin/network/delete', admin.NetworkDelete,
        name='admin:network:delete'),


    url(r'/admin/network/ippool', admin.IPPoolIndex,
        name='admin:network:ippool'),

    url(r'/admin/network/gateway', admin.GatewayIndex,
        name='admin:network:gateway'),

    url(r'/admin/network/gateway/config', admin.GatewayConfig,
        name='admin:network:gateway:config'),

    url(r'/admin/network/portmapping', admin.PortMappingIndex,
        name='admin:network:portmapping'),

]
