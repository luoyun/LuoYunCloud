from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.image.views',

    url(r'^$', 'index', name='index'),
    url(r'^register$', 'register', name='register'),
    url(r'(?P<id>\d+)/$', 'view_image', name='view'),
    url(r'(?P<id>\d+)/ajax/$', 'ajax_image_show', name='ajax_show'),
)
