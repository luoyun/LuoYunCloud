from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.domain.views',

    url(r'^$', 'index', name='index'),

    url(r'^(?P<id>\d+)/start/$', 'domain_control', {'control': 'run'}, name='start'),
    url(r'^(?P<id>\d+)/stop/$', 'domain_control', {'control': 'stop'}, name='stop'),
    url(r'^(?P<id>\d+)/reboot/$', 'domain_control', {'control': 'reboot'}, name='reboot'),
    url(r'^(?P<id>\d+)/conf/$', 'get_domain_conf', name='conf'),
    url(r'^(?P<id>\d+)/config/$', 'get_domain_config', name='config'),
    url(r'^(?P<id>\d+)/osmanager_config/$', 'osmanager_config', name='osmanager_config'),

    url(r'^domain_list/ajax/$', 'domain_list', name='domain_list_ajax'),

    url(r'^add/$', 'add_domain', name='add'),
    url(r'^add/from_image_(?P<image_id>\d+)/$', 'add_domain', name='add_from_image'),
    url(r'^(?P<id>\d+)/$', 'view_domain', name='view'),
    url(r'^(?P<id>\d+)/delete/$', 'delete_domain', name='delete'),
    url(r'^(?P<id>\d+)/edit/$', 'edit_domain', name='edit'),

    url(r'^add_catalog$', 'add_catalog', name='add_catalog'),
    url(r'^catalog/(?P<id>\d+)/$', 'view_catalog', name='view_catalog'),
    url(r'^catalog_ajax/(?P<id>\d+)/$', 'view_catalog_ajax', name='view_catalog_ajax'),
)
