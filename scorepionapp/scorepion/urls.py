#URLS for scorepion mlb API
from django.conf.urls import patterns, url
from scorepion import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),



        )
