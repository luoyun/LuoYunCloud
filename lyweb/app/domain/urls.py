from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.domain.views',

    url(r'^$', 'index', name='index'),
    url(r'^create/simple/$', 'simple_create', name='simple_create'),

    url(r'^(?P<id>\d+)/stop/$', 'domain_control', {'control': 'stop'}, name='stop'),
    url(r'^(?P<id>\d+)/reboot/$', 'domain_control', {'control': 'reboot'}, name='reboot'),
    #url(r'^(?P<id>\d+)/start/$', 'domain_control', {'control': 'start'}, name='start'),
    url(r'^(?P<id>\d+)/run/$', 'domain_control', {'control': 'run'}, name='run'),
    #url(r'^(?P<id>\d+)/update/$', 'domain_control', {'control': 'update'}, name='update'),
    url(r'^(?P<id>\d+)/conf/$', 'get_domain_conf', name='conf'),
    #url(r'^(?P<id>\d+)$', 'view_node', name='view'),
    url(r'^(?P<id>\d+)/show/$', 'show_domain', name='show'),

    url(r'^domain_list/ajax/$', 'domain_list', name='domain_list_ajax'),
)
