from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.xmlrpc.views',

    url(r'^$', 'rpc_handler', name='rpc_handler'),
)
