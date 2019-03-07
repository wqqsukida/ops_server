from django.shortcuts import render,redirect,HttpResponseRedirect
from django.shortcuts import HttpResponse
from django.http import FileResponse
from rbac.models import *
from cmdb import models as cmdb_models
import copy
import json
import traceback
import random
import datetime
import os
from utils.md5 import encrypt
from django.forms import Form,fields,widgets
from .models import *
from django.db.models import Q
from django.urls import reverse
from utils.pagination import Pagination
from django.http.request import QueryDict
from django.conf import settings
from utils.filter_row import Row

#========================================================================#
def init_paginaion(request,queryset):
    # 初始化分页器
    query_params = copy.deepcopy(request.GET)  # QueryDict
    current_page = request.GET.get('page', 1)
    # per_page = config.per_page
    # pager_page_count = config.pager_page_count
    all_count = queryset.count()
    base_url = request.path_info
    page_obj = Pagination(current_page, all_count, base_url, query_params)
    query_set = queryset[page_obj.start:page_obj.end]
    page_html = page_obj.page_html()

    return query_set,page_html
#==========任务模板视图===============
def server_taskmethod_list(request):
    '''
    任务模板列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        queryset = TaskMethod.objects.all()
        script_query = TaskScript.objects.all()
        # 加载分页器
        task_list, page_html = init_paginaion(request, queryset)


        return render(request,'server_taskmethod.html',locals())

    elif request.method == "POST":
        tm_id = request.POST.get("tm_id")
        script_id = TaskMethod.objects.get(id=tm_id).task_script_id
        script_path = TaskScript.objects.get(id=script_id).script_path
        with open(script_path,'r') as f:
            script_content = f.read()
        return HttpResponse(json.dumps(script_content))


def server_taskmethod_add(request):
    result = {}
    if request.method == "POST":
        title = request.POST.get("title")
        run_path = request.POST.get("run_path")
        args = request.POST.get("args")
        content = request.POST.get("content")
        # has_file = request.POST.get("has_file")
        # file_url = request.POST.get("file_url")
        ts_id = request.POST.get("ts_id")
        if title:
            try:
                TaskMethod.objects.create(title=title,run_path=run_path,args=args,
                                          content=content,task_script_id=ts_id)
                result = {"code": 0, "message": "任务模板创建成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "必须指定任务模板名称!"}
    return HttpResponseRedirect('/task/server_taskmethod_list?status={0}&message={1}'.
                                format(result.get("code", ""),
                                       result.get("message", "")))

def server_taskmethod_edit(request):
    if request.method == "GET":
        tid = request.GET.get('tid',None)
        t_obj = TaskMethod.objects.filter(id=tid)
        t_dict = t_obj.values().first()
        t_dict.pop('create_date')

        return HttpResponse(json.dumps(dict(t_dict)))

    elif request.method == "POST":
        tid = request.POST.get("id")
        title = request.POST.get("title",None)
        run_path = request.POST.get("run_path",None)
        args = request.POST.get("args",None)
        content = request.POST.get("content",None)
        # has_file = request.POST.get("has_file")
        # file_url = request.POST.get("file_url")
        ts_id = request.POST.get("ts_id",None)
        try:
            ts_obj = TaskScript.objects.get(id=ts_id)
            t_obj = TaskMethod.objects.get(id=tid)
            form_data = {
                'title':title,
                'run_path':run_path,
                'args':args,
                'content':content,
                'task_script':ts_obj,
                # 'has_file':True if has_file == 'on' else False,
                # 'file_url':file_url
            }

            for k ,v in form_data.items():
                setattr(t_obj,k,v)
                t_obj.save()
            result = {"code": 0, "message": "任务项更新成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/task/server_taskmethod_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def server_taskmethod_del(request):
    if request.method == "GET":
        tid = request.GET.get("tid")
        try:
            TaskMethod.objects.get(id=tid).delete()
            result = {"code": 0, "message": "任务项删除成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/task/server_taskmethod_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))

def server_taskscript_upload(request):
    if request.method == "POST" :
        file_obj = request.FILES.get('task_script')

        file_path = os.path.join(settings.BASE_DIR,'task/task_script')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        script_file_path = os.path.join(file_path, file_obj.name)
        f = open(script_file_path,'wb')
        for c in file_obj.chunks():
            f.write(c)
        f.close()
        try :
            ts_obj = TaskScript.objects.create(name=file_obj.name,script_path=script_file_path)
            server_ip = settings.SERVER_IP
            download_url = 'http://{0}/task/taskscript_download/?tid={1}'.format(server_ip,ts_obj.id)
            setattr(ts_obj,'download_url',download_url)
            ts_obj.save()
            result = {"code": 0, "message": "任务脚本上传成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/task/server_taskmethod_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))

def server_taskscript_download(request):
    if request.method == "GET":
        tid = request.GET.get("tid")
        try:
            ts_obj = TaskScript.objects.filter(id=tid).first()
            file_path = ts_obj.script_path
            file_name = file_path.rsplit('/',1)[-1]
            file = open(file_path,'rb')
            rep = FileResponse(file)
            rep['Content-type'] = 'application/octet-stream'
            rep['Content-Disposition'] = 'attachment;filename=%s'%file_name
            return rep
        except Exception as e:
            print(traceback.format_exc())
            return HttpResponse('DownLoad Error!(%s)'%str(e))

def server_taskscript_del(request):
    if request.method == "POST":
        tid = request.POST.get("tid")
        res = {'status':None,'msg':''}
        try:
            ts_obj = TaskScript.objects.get(id=tid)
            if os.path.exists(ts_obj.script_path):
                os.remove(ts_obj.script_path)
            ts_obj.delete()
            res['status'] = True
        except Exception as e:
            res['status'] = False
            res['msg'] = str(e)
        return HttpResponse(json.dumps(res))

#==========任务会话视图=============
def server_task_session(request):
    '''
    服务器任务会话列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        # fs_id = request.GET.get("sid","")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}
        # if fs_id:
        #     queryset = TaskSession.objects.filter(father_session_id=fs_id)
        #     current_session = TaskSession.objects.filter(id=fs_id)
        # else:
        queryset = TaskSession.objects.all()
        # 加载分页器
        model_list, page_html = init_paginaion(request, queryset)

        page = request.GET.get('page')

        return render(request,'server_task_session.html',locals())

def server_run_session(request):
    '''
    单独执行任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        sid = request.GET.get("mid","")
        s_obj = TaskSession.objects.get(id=sid)
        status = request.GET.get("status")

        # fs_id = request.GET.get("fs_id","")
        page = request.GET.get("page")

        if status == "pause" :
            ServerTask.objects.filter(session_obj=s_obj,status=1).update(
                status=4,finished_date=datetime.datetime.now())
            result = {"code": 2, "message": "子任务会话已被暂停执行 !"}
        elif status == "redo" :
            ServerTask.objects.filter(session_obj=s_obj,status=4).update(
                status=1,finished_date=None
            )
            result = {"code": 0, "message": "子任务会话已恢复执行 !"}
        else:
            # 权限处理
            user_dict = request.session.get('is_login', None)
            if UserProfile.objects.get(name=user_dict['user']).is_admin:
                server_objs = s_obj.server_obj.all()
            else:
                server_objs = s_obj.server_obj.filter(
                    business_unit__roles__userprofile__name=user_dict['user'])
            # 创建任务
            if server_objs:
                try:
                    for t in s_obj.task_obj.all():
                        for s in server_objs:
                            ServerTask.objects.create(server_obj=s,task_obj=t,session_obj=s_obj
                                                      # name=t.title,path=t.run_path,args=t.args,
                                                      )
                    result = {"code": 0, "message": "任务会话执行成功 !"}
                except Exception as e:
                    result = {"code": 1, "message": str(e)}
            else:
                result = {"code": 1, "message": "你没有权限执行该会话下的任务!"}

        return HttpResponseRedirect('/task/server_task_session?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def server_random_run(request):
    '''
    随机执行任务会话里的任务
    :param request:
    :return:
    '''
    if request.method == "GET":
        sid = request.GET.get("sid","")
        s_obj = TaskSession.objects.get(id=sid)

        # fs_id = request.GET.get("fs_id","")
        page = request.GET.get("page")

        # 权限处理
        user_dict = request.session.get('is_login', None)
        if UserProfile.objects.get(name=user_dict['user']).is_admin:
            server_objs = s_obj.server_obj.all()
        else:
            server_objs = s_obj.server_obj.filter(business_unit__roles__userprofile__name=user_dict['user'])

        # 创建任务
        if server_objs:
            try:
                for t in s_obj.task_obj.all():
                    s = random.choice(server_objs)
                    # print(s.hostname,t.title)
                    ServerTask.objects.create(server_obj=s,task_obj=t,session_obj=s_obj,
                                              # name=t.title,path=t.run_path,args=t.args,
                                              )
                result = {"code": 0, "message": "随机执行成功 !"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "你没有权限执行该会话下的任务!"}

        return HttpResponseRedirect('/task/server_task_session?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def server_copy_session(request):
    '''
    复制当前任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        sid = request.GET.get('sid',None)
        # fs_id = request.GET.get("fs_id")
        page = request.GET.get("page")
        try:
            old_ts = TaskSession.objects.filter(id=sid)
            task_objs = old_ts.first().task_obj.all()
            server_objs = old_ts.first().server_obj.all()
            old_val = old_ts.values('is_random', 'title',  'content').first()
            new_ts = TaskSession.objects.create(**old_val)
            new_ts.task_obj.add(*task_objs)
            new_ts.server_obj.add(*server_objs)
            result = {"code": 0, "message": "任务会话复制成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/task/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def server_create_session(request):
    '''
    创建任务会话
    :param request:
    :return:
    '''
    result = {}
    if request.method == "GET":
        server_queryset = cmdb_models.Server.objects.all()
        # 权限处理:添加任务会话时只能指定当前用户属组下的主机
        user_dict = request.session.get('is_login', None)
        if not UserProfile.objects.get(name=user_dict['user']).is_admin:
            server_queryset = cmdb_models.Server.objects.filter(business_unit__roles__userprofile__name=user_dict['user'])
        server_query_list = [{'id':q.id,'manage_ip':q.manage_ip} for q in server_queryset]
        task_queryset = TaskMethod.objects.all()
        task_query_list = [{'id':t.id,'title':t.title} for t in task_queryset]
        res = {'server':server_query_list,'task':task_query_list}
        return HttpResponse(json.dumps(res))

    elif request.method == "POST":
        title = request.POST.get("title")
        sid_list = request.POST.getlist("sids")
        tid_list = request.POST.getlist("tids")
        content = request.POST.get("content")
        is_random = request.POST.get("is_random")
        is_random = True if is_random == 'on' else False

        # father_session_id = request.POST.get("fs") #要修改的fs_id

        # fs_id = request.POST.get("fs_id") #当前页面的fs_id
        page = request.POST.get("page")
        if title:
            try:
                new_ts = TaskSession.objects.create(title=title,content=content,
                                                        is_random=is_random)
                s_objs = cmdb_models.Server.objects.filter(id__in=sid_list)
                t_objs = TaskMethod.objects.filter(id__in=tid_list)
                new_ts.server_obj.add(*s_objs)
                new_ts.task_obj.add(*t_objs)
                result = {"code": 0, "message": "任务会话创建成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "必须指定会话名称!"}
        return HttpResponseRedirect('/task/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def server_edit_session(request):
    '''
    修改任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        mid = request.GET.get('mid',None)

        m_obj = TaskSession.objects.filter(id=mid)
        m_dict = m_obj.values().first()
        m_dict.pop('create_date')

        as_list = cmdb_models.Server.objects.all()
        # 权限处理
        # user_dict = request.session.get('is_login', None)
        # if not UserProfile.objects.get(name=user_dict['user']).is_admin:
        #     as_list = cmdb_models.Server.objects.filter(business_unit__roles__userprofile__name=user_dict['user'])
        ms_list = m_obj.first().server_obj.all()

        as_id = {(s.id,s.manage_ip) for s in as_list}
        ms_id = {(s.id,s.manage_ip) for s in ms_list}

        sfrom_list = [{'id':i[0],'val':i[1]}for i in as_id.difference(ms_id)]
        sto_list = [{'id':i[0],'val':i[1]}for i in ms_id]

        m_dict['sfrom_list'] = sfrom_list
        m_dict['sto_list'] = sto_list
        #===========================================#

        at_list = TaskMethod.objects.all()
        mt_list = m_obj.first().task_obj.all()

        at_id = {(t.id,t.title) for t in at_list}
        mt_id = {(t.id,t.title) for t in mt_list}

        tfrom_list = [{'id':i[0],'val':i[1]}for i in at_id.difference(mt_id)]
        tto_list = [ {'id':i[0],'val':i[1]} for i in mt_id]

        m_dict['tfrom_list'] = tfrom_list
        m_dict['tto_list'] = tto_list

        return HttpResponse(json.dumps(dict(m_dict)))

    elif request.method == "POST":

        mid = request.POST.get("id")
        title = request.POST.get("title",None)
        content = request.POST.get("content",None)
        is_random = request.POST.get("is_random",None)
        is_random = True if is_random == 'on' else False
        server_obj = request.POST.getlist("sids",None)
        task_obj = request.POST.getlist("tids",None)
        # fs = request.POST.get("fs")

        # fs_id = request.POST.get("fs_id")
        page = request.POST.get("page")

        form_data = {
            'title':title,
            'server_obj':server_obj,
            'task_obj':task_obj,
            'content':content,
            'is_random':is_random,
            # 'father_session_id':fs
        }

        m_obj = TaskSession.objects.get(id=mid)
        try:
            for k ,v in form_data.items():
                setattr(m_obj,k,v)
                m_obj.save()
            result = {"code": 0, "message": "任务会话更新成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/task/server_task_session?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def server_del_session(request):
    '''
    删除任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        mid = request.GET.get("mid")

        # fs_id = request.GET.get("fs_id")
        page = request.GET.get("page")
        try:
            TaskSession.objects.get(id=mid).delete()
            result = {"code": 0, "message": "任务会话删除成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/task/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

#==========主机任务状态视图===========
def server_task_status(request,sid="",ssid="",sts_id=""):
    '''
    任务执行列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        # 通知栏
        task_status = request.GET.get("task_status", "")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        # server_id = request.GET.get("sid")
        # secsession_id = request.GET.get("ssid")
        # st_status_id = request.GET.get("sts_id")
        # fsid = request.GET.get("fsid")
        server_id=sid
        session_id=ssid
        st_status_id=sts_id
        # 配置快速组合筛选
        querydict = request.GET
        row = Row(
            [{'id':i[0],'name':i[1]}for i in ServerTask.task_status_choices],
            querydict,
            'task_status'
        )


        search_q = request.GET.get("q","").strip()
        page = request.GET.get('page')
        q_query = Q(Q(task_obj__title__contains=search_q)|
                    Q(task_obj__content__contains=search_q)|
                    Q(server_obj__manage_ip__contains=search_q)|
                    Q(session_obj__title__contains=search_q)
                    # Q(secsession_obj__father_session__title__contains=search_q)
                    )

        if server_id: #从主机列表访问
            server_obj = cmdb_models.Server.objects.get(id=server_id)
            queryset = ServerTask.objects.filter(server_obj=server_obj).order_by('-create_date')
        elif session_id: #从任务会话列表访问
            ss_obj = TaskSession.objects.get(id=session_id)
            if st_status_id == '1':
                queryset = ServerTask.objects.filter(q_query,status=1,session_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '2':
                queryset = ServerTask.objects.filter(q_query,status=2,session_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '3':
                queryset = ServerTask.objects.filter(q_query,status=3,session_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '4':
                queryset = ServerTask.objects.filter(q_query,status=4,session_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '5':
                queryset = ServerTask.objects.filter(q_query,status=5,session_obj=ss_obj).order_by('-create_date')
            else:
                queryset = ServerTask.objects.filter(q_query,session_obj=ss_obj).order_by('-create_date')
        # elif fsid:
        #     fs_obj =  TaskSession.objects.filter(id=fsid)
        #     ss_objs = fs_obj.values('task_secsession__id')
        #     ssid_list = [t['task_secsession__id'] for t in ss_objs]
        #     if st_status_id == '1':
        #         queryset = ServerTask.objects.filter(q_query,status=1,secsession_obj_id__in=ssid_list).order_by('-create_date')
        #     elif st_status_id == '2':
        #         queryset = ServerTask.objects.filter(q_query,status=2,secsession_obj_id__in=ssid_list).order_by('-create_date')
        #     elif st_status_id == '3':
        #         queryset = ServerTask.objects.filter(q_query,status=3,secsession_obj_id__in=ssid_list).order_by('-create_date')
        #     elif st_status_id == '4':
        #         queryset = ServerTask.objects.filter(q_query,status=4,secsession_obj_id__in=ssid_list).order_by('-create_date')
        #     elif st_status_id == '5':
        #         queryset = ServerTask.objects.filter(q_query,status=5,secsession_obj_id__in=ssid_list).order_by('-create_date')
        #     else:
        #         queryset = ServerTask.objects.filter(q_query,secsession_obj_id__in=ssid_list).order_by('-create_date')
        else:
            queryset = ServerTask.objects.filter(q_query).order_by('-create_date')
        # 权限处理
        user_dict = request.session.get('is_login', None)
        if not UserProfile.objects.get(name=user_dict['user']).is_admin:
            queryset = queryset.filter(server_obj__business_unit__roles__userprofile__name=user_dict['user'])
        # 加载组合筛选
        if task_status:
            queryset = queryset.filter(status=task_status)
        # 加载分页器
        task_list, page_html = init_paginaion(request, queryset)

        return render(request,'server_task.html',locals())
    elif request.method == "POST":
        task_id = request.POST.get("task_id")
        task_obj = ServerTask.objects.get(id=task_id)
        t_res = task_obj.task_res
        res = {'res':'task running......'}
        if t_res:
            import ast
            res = ast.literal_eval(t_res)  # 字符串转换字典

        return HttpResponse(json.dumps(res))

def server_task_reload(request):
    if request.method == "GET":
        tid = request.GET.get("tid")

        # fsid = request.GET.get("fsid","")
        ssid = request.GET.get("ssid","")
        sts_id = request.GET.get("sts_id","")
        page = request.GET.get("page","")
        server_id = request.GET.get("sid","")

        try:
            ServerTask.objects.filter(id=tid).update(status=1,finished_date=None)
            result = {"code":0, "message":"任务恢复成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/task/server_task_status/{0}/{1}/{2}/'
                                    '?status={3}&message={4}&page={5}'.
                                    format(server_id,ssid,sts_id,
                                           result.get("code", ""),
                                           result.get("message", ""),
                                           page,
                                           ))

def server_task_del(request):
    if request.method == "GET":
        tid = request.GET.get("tid")

        # fsid = request.GET.get("fsid","")
        ssid = request.GET.get("ssid","")
        sts_id = request.GET.get("sts_id","")
        page = request.GET.get("page","")
        server_id = request.GET.get("sid","")

        try:
            ServerTask.objects.filter(id=tid).delete()
            result = {"code":0, "message":"任务删除成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/task/server_task_status/{0}/{1}/{2}/'
                                    '?status={3}&message={4}&page={5}'.
                                    format(server_id,ssid,sts_id,
                                           result.get("code", ""),
                                           result.get("message", ""),
                                           page,
                                           ))