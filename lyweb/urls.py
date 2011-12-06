from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^lyweb/', include('lyweb.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('lyweb.app.home.urls', namespace='home')),
    url(r'^image/', include('lyweb.app.image.urls', namespace='image')),
    url(r'^node/', include('lyweb.app.node.urls', namespace='node')),
    url(r'^domain/', include('lyweb.app.domain.urls', namespace='domain')),
    url(r'^job/', include('lyweb.app.job.urls', namespace='job')),
    #url(r'^xmlrpc/', include('lyweb.app.xmlrpc.urls', namespace='xmlrpc')),
)


if (settings.DEBUG):
    urlpatterns += patterns ('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
