# /usr/bin/env python
# -*- coding:utf-8 -*-
# Author  : wuyifei
# Data    : 10/15/18 10:01 AM
# FileName: views_cbv.py
import datetime
import json
import time
import os
import threading
import copy
from cmdb import models
from firmware import models as fw_models
from task import models as task_models
from django.db.models import Q
from .plugins import PluginManger
from utils.md5 import encrypt
from django.conf import settings


from django.shortcuts import render,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from rest_framework.views import APIView
from rest_framework.response import Response


key = settings.API_TOKEN

def api_auth(func):
    def inner(request,*args,**kwargs):
        server_float_ctime = time.time()
        auth_header_val = request.META.get('HTTP_AUTH_TOKEN')
        # 841770f74ef3b7867d90be37c5b4adfc|1506571253.9937866
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']

        if auth_header_val:
            client_md5_str, client_ctime = auth_header_val.split('|', maxsplit=1)
            client_float_ctime = float(client_ctime)

            # 第一关
            if (client_float_ctime + 20) < server_float_ctime:
                res = { 'code': 5, 'msg': 'token已经过期!'}
                print('[{0}]:{1}'.format(clien_ip, res))
                return HttpResponse(json.dumps(res))

            # 第二关：
            server_md5_str = encrypt("%s|%s" % (key, client_ctime,))
            if server_md5_str != client_md5_str:
                res = {'code': 6, 'msg': 'token验证失败!'}
                print('[{0}]:{1}'.format(clien_ip, res))
                return HttpResponse(json.dumps(res))

            return func(request,*args,**kwargs)
        else:
            res = {'code': 7, 'msg': '找不到token,请求失败!'}
            print('[{0}]:{1}'.format(clien_ip, res))
            return HttpResponse(json.dumps(res))

    return inner

SIGN_RECORD = {}
class APIAuthView(APIView):
    def dispatch(self, request, *args, **kwargs):
        server_float_ctime = time.time()
        auth_header_val = request.META.get('HTTP_AUTH_TOKEN')
        # 841770f74ef3b7867d90be37c5b4adfc|1506571253.9937866
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']

        if auth_header_val:
            client_md5_str, client_ctime = auth_header_val.split('|', maxsplit=1)
            client_float_ctime = float(client_ctime)
            # print(server_float_ctime - client_float_ctime)
            # if (client_float_ctime + 20) < server_float_ctime :
            #     res = {'code': 5, 'msg': 'token已经过期!'}
            #     print('[{0}]:{1}'.format(clien_ip, res))
            #     return HttpResponse(json.dumps(res))

            # if client_md5_str in SIGN_RECORD:
            #     res = {'code': 6, 'msg': 'token已被使用!'}
            #     print('[{0}]:{1}'.format(clien_ip, res))
            #     return HttpResponse(json.dumps(res))

            server_md5_str = encrypt("%s|%s" % (key, client_ctime,))
            if server_md5_str != client_md5_str:
                res = {'code': 7, 'msg': 'token验证失败!'}
                print('[{0}]:{1}'.format(clien_ip, res))
                return HttpResponse(json.dumps(res))

            # SIGN_RECORD[server_md5_str] = client_ctime
            # SIGN_RECORD_copy = copy.deepcopy(SIGN_RECORD)
            # for k,v in SIGN_RECORD_copy.items():
            #     if float(v) + 20 < float(client_ctime):
            #         SIGN_RECORD.pop(k)

            # print(SIGN_RECORD)
        else:
            res = {'code': 8, 'msg': '找不到token,请求失败!'}
            print('[{0}]:{1}'.format(clien_ip, res))
            return HttpResponse(json.dumps(res))

        return super().dispatch(request, *args, **kwargs)

class ServerView(APIAuthView):
    # @method_decorator(api_auth)
    def get(self,request,*args,**kwargs):
        current_date = datetime.date.today()
        # 获取今日未采集的主机列表
        query_list = models.Server.objects.filter(
            Q(Q(latest_date=None)|Q(latest_date__lt=current_date))   & Q(server_status_id=2)
        )
        host_list = list(query_list.values('hostname'))
        query_list.update(server_status_id=3)

        return HttpResponse(json.dumps(host_list))

    # @method_decorator(api_auth)
    def post(self,request,*args,**kwargs):
        # 客户端提交的最新资产数据
        server_dict = json.loads(request.body.decode('utf-8'))
        # 获取客户端ip
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']

        # print(server_dict)
        # 检查server表中是否有当前资产信息【主机名是唯一标识】
        if not server_dict['basic']['status']:
            return HttpResponse('Server Post Status Error!')
        if clien_ip:
            server_dict['basic']['data']['manage_ip'] = clien_ip
        manager = PluginManger()
        response = manager.exec(server_dict)
        print('[{0}][Server_info]Response to[{1}]:{2}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                 ,clien_ip,response))
        return HttpResponse(json.dumps(response))

class TaskView(APIAuthView):
    # @method_decorator(api_auth)
    def get(self,request,*args,**kwargs):
        return HttpResponse('Error api method!')

    # @method_decorator(api_auth)
    def post(self,request,*args,**kwargs):
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']
        res = json.loads(request.body.decode('utf-8'))    #结果必须为字典形式
        stask_res = res.get('stask_res')
        stask_id = res.get('stask_id')
        s_obj = models.Server.objects.filter(cert_id=res.get('cert_id')).first()
        #即时返回当前主机执行任务的状态，更新到task表
        models.FocusTask.objects.update_or_create(server_obj=s_obj,defaults=stask_res)
        #如果返回存在stask_id且状态0,3的任务，更新servertask表
        if stask_id:
            if stask_res.get('status') == '0':
                status_code = 2
            else :
                status_code = stask_res.get('status')
            st_obj = task_models.ServerTask.objects.filter(id=stask_id)
            st_obj.update(status=status_code,
                          msg=stask_res.get('msg'),
                          elapsed=stask_res.get('elapsed'),
                          finished_date=datetime.datetime.now()
                          )
        ####################################添加推送主机任务请求######################################
        response = {}

        server_task_query_list = task_models.ServerTask.objects.filter(server_obj=s_obj,status=1).\
            order_by('create_date')
        server_runing_task = task_models.ServerTask.objects.filter(server_obj=s_obj,status=5)
        st = server_task_query_list.first()    # 只推送一个任务
        if st and not server_runing_task:
            '''
            存在可推送任务且当前主机没有执行中的任务
            '''
            response.update({'stask': {'stask_id': st.id,
                                       'name': st.task_obj.title,
                                       'path':st.task_obj.run_path,
                                       'args_str': st.task_obj.args,
                                       'download_url':st.task_obj.task_script.download_url},
                             })
            task_models.ServerTask.objects.filter(id=st.id).update(status=5, create_date=datetime.datetime.now())
        print('[{0}][ServerTask]Response to[{1}]:{2}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                             clien_ip, response))
        return HttpResponse(json.dumps(response))

class UtaskView(APIAuthView):
    # @method_decorator(api_auth)
    def get(self,request,*args,**kwargs):
        return HttpResponse('Error api method!')

    # @method_decorator(api_auth)
    def post(self,request,*args,**kwargs):
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']

        rep = json.loads(request.body.decode('utf-8'))    #结果必须为字典形式
        res = rep.get("update_res")
        if res:
            ut_obj = fw_models.Update_task.objects.filter(id=res.get('utask_id'))
            ut_obj.update(status=res.get('status_code'),
                          run_time=res.get('run_time'),
                          update_res=res.get("message"))
        ####################################添加推送升级任务请求######################################
        cert_id = rep.get("cert_id")
        response = {}
        server_obj = models.Server.objects.filter(cert_id=cert_id).first()
        ssd_objs = models.Nvme_ssd.objects.filter(server_obj=server_obj)
        update_task_query_list = fw_models.Update_task.objects.filter(ssd_obj__in=ssd_objs,status=1).\
            order_by('create_date')
        server_runing_update = fw_models.Update_task.objects.filter(ssd_obj__in=ssd_objs,status=5)
        ut = update_task_query_list.first()    # 只推送一个任务
        if ut and not server_runing_update:
            '''
            存在可推送任务且当前主机没有执行中的任务
            '''
            response.update({'utask':{
                'utask_id':ut.id,
                'node':ut.ssd_obj.node,
                'img_type':ut.img_obj.get_image_type_display(),
                'download_url':ut.img_obj.download_url,
                'args_str':''},
            })
            fw_models.Update_task.objects.filter(id=ut.id).update(status=5,create_date=datetime.datetime.now())
        print('[{0}][Update]Response to[{1}]:{2}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                     clien_ip, response))
        return HttpResponse(json.dumps(response))