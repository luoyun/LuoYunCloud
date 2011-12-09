from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.home.views',

    url(r'^$', 'index', name='index'),
    url(r'^accounts/login/$', 'login', name='login'),
    url(r'^accounts/logout/$', 'logout', name='logout'),
    url(r'^ajax_new_jobs/$', 'ajax_new_jobs', name='ajax_new_jobs'),
)
