from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.node.views',

    url(r'^$', 'index', name='index'),
    url(r'^register$', 'register', name='register'),
    url(r'^(?P<id>\d+)$', 'view_node', name='view'),
    url(r'^(?P<id>\d+)/update/$', 'node_control', {'control': 'update'}, name='update'),

    url(r'^node_list/ajax/$', 'node_list', name='node_list_ajax'),
)
