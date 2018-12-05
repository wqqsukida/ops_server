# /usr/bin/env python
# -*- coding:utf-8 -*-
# Author  : wuyifei
# Data    : 12/4/18 4:58 PM
# FileName: cron_task.py
import datetime
from cmdb.models import Server
from django.db.models import Q

def refresh_server():
    now = datetime.datetime.now()
    start = now - datetime.timedelta(hours=0, minutes=30, seconds=0)
    # 获取30min未采集的主机列表
    query_list = Server.objects.filter(
        Q(Q(latest_date=None) | Q(latest_date__lt=start)) & Q(server_status_id=2)
    )
    host_list = list(query_list.values('hostname'))
    query_list.update(server_status_id=3)
    print('30min not send host:%s' % host_list)