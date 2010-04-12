# -*- coding: utf-8 -*-
from django.conf.urls.defaults import handler404, handler500, include, patterns, url # all imports need because http://code.djangoproject.com/ticket/5350

urlpatterns = patterns('',
    (r'car/$',                   'rest_client_test.views.car'),
)