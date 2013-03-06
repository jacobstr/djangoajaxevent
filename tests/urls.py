from django.conf.urls.defaults import *
from views import *

from ajax_event.urls import urlpatterns 

# Selective C&P from django.tests.regressionstests.urls
urlpatterns += patterns('',
    url(r'^special_chars/(.+)/$', empty_view, name="special"),
    url(r'^price/\$(\d+)/$', empty_view, name="price"),
    url(r'^price/[$](\d+)/$', empty_view, name="price2"),
    url(r'^price/[\$](\d+)/$', empty_view, name="price3"),
    url(r'^product/(?P<product>\w+)\+\(\$(?P<price>\d+(\.\d+)?)\)/$',
            empty_view, name="product"),
    url(r'^headlines/(?P<year>\d+)\.(?P<month>\d+)\.(?P<day>\d+)/$', empty_view,
            name="headlines"),
    url(r'^windows_path/(?P<drive_name>[A-Z]):\\(?P<path>.+)/$', empty_view,
            name="windows"),
    )

