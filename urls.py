from django.conf.urls.defaults import *
from django.contrib import comments

# See settings.py for various LOGIN url settings.
urlpatterns = patterns('',
    url(r'^reverse/(\w+)/$','ajax_event.views.url_reverse',name='ajax_reverse'),
    url(r'^resolve/(\w+)/$','ajax_event.views.url_resolve',name='ajax_resolve'),
)
