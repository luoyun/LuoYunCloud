from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.home.views',

    url(r'^$', 'index', name='index'),
    url(r'^ajax/domain_list/$', 'ajax_domain_list'),
    url(r'^accounts/login/$', 'login', name='login'),
    url(r'^accounts/logout/$', 'logout', name='logout'),
)
