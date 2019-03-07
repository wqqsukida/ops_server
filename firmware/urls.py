"""auto_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from . import views
urlpatterns = [
    url(r'^version_info', views.version_info),
    url(r'^version_add', views.version_add),
    url(r'^version_edit', views.version_edit),
    url(r'^version_del', views.version_del),
    url(r'^dev_list', views.dev_list),
    url(r'^dev_add', views.dev_add),
    url(r'^dev_del', views.dev_del),
    url(r'^dev_edit', views.dev_edit),
    url(r'^img_list', views.img_list),
    url(r'^img_add', views.img_add),
    url(r'^img_del', views.img_del),
    url(r'^img_edit', views.img_edit),
    url(r'^img_enabled', views.img_enabled),
    url(r'^image_download', views.image_download),
    url(r'^version_update', views.version_update),
    url(r'^ssd_update', views.ssd_update),
    url(r'^host_update', views.host_update),
    url(r'^update_history', views.update_history),
    url(r'^client_update', views.client_update),

]
