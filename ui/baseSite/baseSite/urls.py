from django.conf.urls import patterns, include, url
from baseSite.views import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # home index page
    ('^$', home),
    ('^home/$', home),
    # url(r'^baseSite/', include('baseSite.foo.urls')),

    # FireWorks index
    ('^fw/$', fw),
    # FireWork info pages
    (r'^fw/(\d+)/$', fw_id),
    # (r'^fw/(\d+)/(more|less|all)/$', fw), 

    # WorkFlows index
    ('^wf/$', wf),
    # WorkFlow info pages
    (r'^wf/(\d+)/$', wf_id),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
