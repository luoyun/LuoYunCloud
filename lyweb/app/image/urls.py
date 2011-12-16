from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.image.views',

    url(r'^$', 'index', name='index'),

    url(r'^add/$', 'add_image', name='add'),
    url(r'^(?P<id>\d+)/$', 'view_image', name='view'),
    url(r'^(?P<id>\d+)/edit/$', 'edit_image', name='edit'),
    url(r'^(?P<id>\d+)/delete/$', 'delete_image', name='delete'),


    url(r'^add_catalog/$', 'add_catalog', name='add_catalog'),
    url(r'^catalog/(?P<id>\d+)/$', 'view_catalog', name='view_catalog'),
    url(r'^catalog_ajax/(?P<id>\d+)/$', 'view_catalog_ajax', name='view_catalog_ajax'),


    url(r'^add_origin/$', 'add_origin', name='add_origin'),
    url(r'^origin/(?P<id>\d+)/$', 'origin', name='origin'),


)
