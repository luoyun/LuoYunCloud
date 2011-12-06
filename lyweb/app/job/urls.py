from django.conf.urls.defaults import *

urlpatterns = patterns('lyweb.app.job.views',

    url(r'^$', 'index', name='index'),
    url(r'^job_list/ajax/$', 'job_list', name='job_list_ajax'),
)
