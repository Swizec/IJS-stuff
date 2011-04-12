from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^WebUI/', include('WebUI.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),

    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    (r'^$', 'Browse.views.begin'),
    (r'^add_feed/$', 'Browse.views.add_feed'),
    (r'^create_feed/$', 'Browse.views.create_feed'),
    (r'^list_dir/$', 'Browse.views.list_dir'),
    (r'^update_feed/$', 'Browse.views.update_feed'),
    (r'^fetch_feed/$', 'Browse.views.fetch_feed'),
    (r'^delete_item/$', 'Browse.views.delete_item'),
    (r'^add_item/$', 'Browse.views.add_item'),
)
