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
    url(r'^add_focus', views.add_focus),  # 首页添加关注主机
    url(r'^del_focus', views.del_focus),  # 首页删除关注主机
    url(r'^add_comment', views.add_comment),  # 首页添加主机备注信息
    url(r'^asset_list', views.asset_list),
    url(r'^asset_detail', views.asset_detail), #主机详情
    url(r'^asset_add', views.asset_add),
    url(r'^asset_del', views.asset_del),
    url(r'^asset_update', views.asset_update),
    url(r'^asset_change_log', views.asset_change_log), #主机变更记录
    url(r'^asset_run_tasks', views.asset_run_tasks), #批量修改主机
    url(r'^tag_add', views.tag_add),    #添加标签
    url(r'^tag_del', views.tag_del),    #删除标签
    url(r'^tag_edit', views.tag_edit),  #修改标签

    url(r'^ssd_list', views.ssd_list), #SSD列表
    url(r'^ssd_smartlog', views.ssd_smartlog), #SSD查看smart_log

]
