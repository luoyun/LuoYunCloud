from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.image.views',

    url(r'^$', 'index', name='index'),
    url(r'^add/$', 'add_image', name='add'),
    url(r'^add_catalog/$', 'add_catalog', name='add_catalog'),
    url(r'catalog/(?P<id>\d+)/$', 'catalog', name='catalog'),
    url(r'(?P<id>\d+)/$', 'view_image', name='view'),

    url(r'(?P<id>\d+)/ajax/$', 'ajax_image_show', name='ajax_show'),



)
