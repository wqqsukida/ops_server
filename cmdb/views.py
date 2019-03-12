from django.shortcuts import render,redirect,HttpResponseRedirect
from django.shortcuts import HttpResponse
from django.http import FileResponse
from rbac.models import *
from rbac.service.init_permission import init_permission
import copy
import json
import random
import datetime
import os
import tablib
from utils.md5 import encrypt
from django.forms import Form,fields,widgets
from .models import *
from django.db.models import Q
from django.urls import reverse
from utils.pagination import Pagination
from django.http.request import QueryDict
from django.conf import settings
from utils.filter_row import Row
from django.forms.models import model_to_dict
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
#========================================================================#
class LoginForm(Form):
    username = fields.CharField(
        required=True,
        error_messages={'required':'*用户名不能为空'},
        widget=widgets.TextInput(attrs={'class':'form-control uname',
                                        'type':'text',
                                        'id':'inputUsername3',
                                        'placeholder':'用户名',
                                        'name':'username'
                                        })
    )
    password = fields.CharField(
        required=True,
        error_messages={'required': '*密码不能为空'},
        widget = widgets.PasswordInput(attrs={'class':'form-control pword m-b',
                                        'id':'inputPassword3',
                                        'placeholder':'密码',
                                        'name':'password'
                                        })
    )

    code = fields.CharField(
        required=True,
        error_messages={'required': '*验证码不能为空'},
        widget = widgets.TextInput(attrs={'class':'form-control',
                                        'id':'inputCode',
                                        'placeholder':'验证码',
                                        'name':'code',
                                        'style':'width:55%;display:inline-block'
                                        }),

    )
#========================================================================#
def login(request):
    '''
    login登录验证函数
    '''
    if request.method == "GET":
        form = LoginForm()
        return render(request,'login_v2.html',{'form':form})
    else:
        response = {'status': True, 'data': None, 'msg': None}
        form = LoginForm(request.POST)
        if form.is_valid():
            user = request.POST.get('username',None)  #获取input标签里的username的值 None：获取不到不会报错
            pwd = request.POST.get('password',None)
            code = request.POST.get('code',None)
            # print(code,request.session['keep_valid_code'])

            if  code.lower() == request.session['keep_valid_code'].lower(): #比对验证码

                pwd = encrypt(pwd) #md5加密密码字符串
                user_obj = AdminInfo.objects.filter(username=user, password=pwd).first()

                if user_obj:
                    role = user_obj.user.roles.values('title')
                    # print(role)
                    if role:
                        role = role.first().get('title')
                    else:
                        role = '访客'
                    request.session['is_login'] = {'user': user_obj.user.name, 'role': role}  # 仅作为登录后用户名和身份显示session
                    init_permission(user_obj, request)
                    response['data'] = {}
                else:
                    response['status'] = False
                    response['msg'] = {'password': ['*用户名或者密码错误']}
            else:
                response['status'] = False
                response['msg'] = {'code': ['*请填写正确的验证码']}
        else:
            response['status'] = False
            response['msg'] = form.errors
        # print(response)
        return HttpResponse(json.dumps(response))

def logout(request):
    '''
    logout删除session函数
    '''
    request.session.clear() #删除session
    return HttpResponseRedirect('/login/')

def forbidden(request):
    return render(request,'403.html')

def index(request):
    '''
    index页面函数
    '''
    user_dict = request.session.get('is_login', None)
    username = user_dict['user']
    user_obj = UserProfile.objects.get(name=username)
    user_role = user_dict['role']
    # print('---当前登录用户/角色--->',username,user_role)
    return render(request,'index.html',locals())


def index_v3(request):
    '''
    首页
    :param request:
    :return:
    '''
    if request.method == "GET":
        page = request.GET.get("page")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code": int(status), "message": message}



        user_dict = request.session.get('is_login', None)
        user_obj = UserProfile.objects.get(name=user_dict['user'])
        focus_query = user_obj.servers.all().order_by('-create_at')
        search_q = request.GET.get('q', '')

        if search_q:
            focus_query = focus_query.filter(manage_ip__contains=search_q)
        # 加载分页器
        queryset, page_html = init_paginaion(request, focus_query)

        return render(request,'index_v3.html',locals())

def add_focus(request):
    user_dict = request.session.get('is_login', None)
    user_obj = UserProfile.objects.get(name=user_dict['user'])
    if request.method == "POST":

        host_lists = request.POST.getlist('host_lists')
        for server_id in host_lists:
            user_obj.servers.add(Server.objects.get(id=server_id))

        return HttpResponseRedirect('/index_v3/')

    elif request.method == "GET":
        query = Server.objects.all()
        focus_query = user_obj.servers.all()

        all_hosts = {(h.id,h.manage_ip)for h in query}
        focus_hosts = {(h.id,h.manage_ip) for h in focus_query}
        hosts = all_hosts - focus_hosts
        return HttpResponse(json.dumps(list(hosts)))

def del_focus(request):
    user_dict = request.session.get('is_login', None)
    user_obj = UserProfile.objects.get(name=user_dict['user'])
    if request.method == "GET":
        host_id = request.GET.get('host_id')
        server_obj = Server.objects.get(id=host_id)
        user_obj.servers.remove(server_obj)
    elif request.method == "POST":
        id_list = request.POST.getlist("input_chk", None)
        print(id_list)
        server_objs = Server.objects.filter(id__in=id_list)
        for s in server_objs:
            user_obj.servers.remove(s)

    return HttpResponseRedirect('/index_v3/')

def add_comment(request):
    if request.method == "POST":
        sid = request.POST.get("sid")
        comment = request.POST.get("comment")

        try:
            s_obj = Server.objects.get(id=sid)
            setattr(s_obj,'comment',comment)
            s_obj.save()
            result = {"code": 0, "message": "添加备注成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/index_v3/?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   ))

#========================================================================#
def asset_list(request):
    if request.method == "GET":
        page = request.GET.get("page")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        search_q = request.GET.get('q','')
        user_dict = request.session.get('is_login', None)
        # print(user_dict)
        #配置快速组合筛选
        server_status_id = request.GET.get('server_status_id')
        business_unit = request.GET.getlist('business_unit')
        tags = request.GET.getlist('tags')
        querydict = request.GET
        row = Row(
            BusinessUnit.objects.all().values(),
            querydict,
            'business_unit'
        )
        row.is_multi = True
        ss_row = Row(
            [{'id':i[0],'name':i[1]} for i in Server.server_status_choices],
            querydict,
            'server_status_id'
        )
        tag_row = Row(
            Tag.objects.all().values(),
            querydict,
            'tags'
        )
        #搜索
        if UserProfile.objects.get(name=user_dict['user']).is_admin :
            queryset = Server.objects.filter(Q(Q(hostname__contains=search_q) |
                                               Q(sn__contains=search_q) |
                                               Q(manage_ip__contains=search_q) |
                                               Q(os_platform__contains=search_q) |
                                               Q(idc__name__contains=search_q) |
                                               Q(business_unit__name__contains=search_q) |
                                               Q(tags__name__contains=search_q))).distinct().order_by("-create_at")
        else:
            queryset = Server.objects.filter(Q(Q(hostname__contains=search_q) |
                                               Q(sn__contains=search_q) |
                                               Q(manage_ip__contains=search_q) |
                                               Q(os_platform__contains=search_q) |
                                               Q(idc__name__contains=search_q) |
                                               Q(business_unit__name__contains=search_q) |
                                               Q(tags__name__contains=search_q)),
                       business_unit__roles__userprofile__name=user_dict['user']).distinct().order_by("-create_at")
        # 加载快速组合筛选
        if business_unit:
            queryset = queryset.filter(business_unit__in=business_unit).distinct().order_by("-create_at")
        if server_status_id:
            queryset = queryset.filter(server_status_id=server_status_id).distinct().order_by("-create_at")
        if tags:
            queryset = queryset.filter(tags__in=tags).distinct().order_by("-create_at")
        idc_list = IDC.objects.all()
        tag_list = Tag.objects.all()
        business_list = BusinessUnit.objects.all()
        #导出表格
        export = request.GET.get("export")
        if export:
            if export == "xlsx":
                headers = ('id','cert_id','comment','idc_id','cabinet_num','cabinet_order',
                           'server_status_id','host_name','nickname','sn','manufacturer','model',
                           'manage_ip','os_platform','os_version','cpu_count','cpu_physical_count',
                           'cpu_model','create_at','latest_date','client_version')
                data = list(queryset.values_list())
            else:
                return HttpResponseRedirect('/403/')
            try:
                data = tablib.Dataset(*data, headers=headers)
            except Exception as e:
                result = {"code": 1, "message": "导出失败：{0}".format(str(e))}
                return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                                            format(result.get("code", ""),
                                                   result.get("message", ""),
                                                   page))

            response = HttpResponse(data.xlsx)
            response['Content-type'] = 'application/octet-stream'
            response["Content-Disposition"] = "attachment;filename=machines.xlsx;"
            return response
        # 加载分页器
        queryset, page_html = init_paginaion(request, queryset)

        return render(request,'asset.html',locals())
    elif request.method == "POST":
        queryset = Server.objects.all()
        host_query_list = [{'id':q.id,'manage_ip':q.manage_ip} for q in queryset if q.nvme_ssd.all()]

        return HttpResponse(json.dumps(host_query_list))

def asset_run_tasks(request):
    if request.method == "POST":
        page = request.POST.get("page")
        id_list = request.POST.getlist("input_chk",None)
        # print('run_actions id :%s'%id_list)
        server_objs = Server.objects.filter(id__in=id_list)
        server_status_id = request.POST.get("status_ids",None)
        tags = request.POST.getlist("tags",None)
        business_unit = request.POST.getlist("business_units",None)
        del_hosts = request.POST.get("del_hosts")
        if server_objs:
            try:
                if server_status_id:
                    server_objs.update(server_status_id=server_status_id)
                    code = 0
                    msg="成功修改主机状态！"
                elif tags:
                    for s in server_objs:
                        setattr(s,'tags',tags)
                        s.save()
                    code = 0
                    msg="成功修改主机标签！"
                elif business_unit:
                    for s in server_objs:
                        setattr(s,'business_unit',business_unit)
                        s.save()
                    code = 0
                    msg="成功修改主机组！"
                elif del_hosts:
                    server_objs.delete()
                    code = 0
                    msg="成功删除主机！"
                else:
                    code = 1
                    msg = "没有可执行的任务！"
                result = {"code": code, "message": msg}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "请至少选择一个主机!!"}
        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def asset_detail(request):
    result = {}
    if request.method == "GET":
        server_id = request.GET.get("id",None)
        server_obj = Server.objects.filter(id=server_id).first()
        if server_obj:
            memory_query_list = Memory.objects.filter(server_obj=server_obj)
            nic_query_list = NIC.objects.filter(server_obj=server_obj)
            disk_query_list = Disk.objects.filter(server_obj=server_obj)
            ssd_query_list = Nvme_ssd.objects.filter(server_obj=server_obj)
            result = {"code": 0, "message": "找到资产"}
        else:
            result = {"code": 1, "message": "未找到指定资产"}

        return render(request,'asset_detail.html',locals())
    else:
        pass

def asset_add(request):
    result = {}
    if request.method == "POST":
        page = request.POST.get('page')
        hostname = request.POST.get('hostname',None)
        sn = request.POST.get('sn',None)
        server_status_id = request.POST.get('server_status_id',None)
        if hostname:
            try:
                Server.objects.create(hostname=hostname,sn=sn,
                                      server_status_id=server_status_id)
                result = {"code": 0, "message": "创建主机成功！"}
            except Exception as e:
                result = {"code": 1, "message":e }
        else:
            result = {"code": 1, "message": "主机名不能为空！"}
        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def asset_del(request):
    if request.method == "GET":
        id = request.GET.get("server_id",None)
        page = request.GET.get("page")
        try:
            Server.objects.get(id=id).delete()
            result = {"code": 0, "message": "删除主机成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def asset_update(request):
    if request.method == "GET":
        res = {}
        id = request.GET.get("server_id",None)

        server_obj = Server.objects.filter(id=id)


        server_dict = server_obj.values().first()
        if server_dict:
            business_unit = server_obj.first().business_unit.all()
            bid_list = [b.id for b in business_unit]
            tags = server_obj.first().tags.all()
            tid_list = [t.id for t in tags]

            server_dict['business_unit'] = bid_list
            server_dict['tags'] = tid_list

            server_dict['latest_date'] = str(server_dict['latest_date'])
            server_dict['create_at'] = str(server_dict['create_at'])
            res = dict(server_dict)
        return HttpResponse(json.dumps(res))

    elif request.method == "POST":

        result = {}
        page = request.POST.get('page')
        id = request.POST.get("id",None)

        nickname = request.POST.get("nickname",None)
        sn = request.POST.get("sn",None)
        manufacturer = request.POST.get("manufacturer",None)
        model = request.POST.get("model",None)
        manage_ip = request.POST.get("manage_ip",None)
        os_platform = request.POST.get("os_platform",None)
        os_version = request.POST.get("os_version",None)

        server_status_id = request.POST.get("server_status_id",None)
        tags = request.POST.getlist("tags",None)
        business_unit = request.POST.getlist("business_unit",None)
        idc = request.POST.get("idc",None)

        val_dic = {'data':{'nickname':nickname,'sn':sn,'manufacturer':manufacturer,
                   'model':model,'manage_ip':manage_ip,'os_platform':os_platform,
                   'os_version':os_version,'server_status_id':server_status_id,
                   'tags':tags,'business_unit':business_unit,'idc_id':idc}}

        try:
            from api.plugins import server
            obj = server.Server(server_obj=Server.objects.get(id=id),basic_dict=val_dic,
                          board_dict={'data':{}})
            obj.user_obj = UserProfile.objects.get(name=request.session['is_login']['user'])
            obj.process()
            result = {"code": 0, "message": "更新主机成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def asset_change_log(request):
    if request.method == "GET":
        res = []
        id = request.GET.get("server_id",None)
        record_list = ServerRecord.objects.filter(server_obj_id=id).order_by('-create_at')
        if record_list:
            for record in record_list:
                res_dic = {}
                res_dic['content'] = record.content
                if record.creator:
                    res_dic['creator'] = record.creator.name
                else:
                    res_dic['creator'] = '自动上报'

                res_dic['create_at'] = str(record.create_at)
                res.append(res_dic)

        return HttpResponse(json.dumps(res))

def tag_add(request):
    if request.method == "POST":
        page = request.POST.get('page')
        name = request.POST.get('name',None)
        if name:
            try:
                Tag.objects.create(name=name)
                result = {"code": 0, "message": "创建标签成功！"}
            except Exception as e:
                result = {"code": 1, "message":e }
        else:
            result = {"code": 1, "message": "标签名不能为空！"}
        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def tag_del(request):
    if request.method == "GET":
        id = request.GET.get("tid",None)
        page = request.GET.get("page")
        try:
            Tag.objects.get(id=id).delete()
            result = {"code": 0, "message": "删除标签成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def tag_edit(request):
    if request.method == "POST":
        page = request.POST.get('page')
        id = request.POST.get("id",None)
        name = request.POST.get("name",None)
        try:
            tag_obj = Tag.objects.filter(id=id)
            tag_obj.update(name=name)
            result = {"code": 0, "message": "修改标签成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

#========================================================================#
def ssd_list(request):
    if request.method == "GET":
        page = request.GET.get("page")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        server_id = request.GET.get("sid")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        search_q = request.GET.get('q','').strip()
        q_query = Q(Q(node__contains=search_q)|
                    Q(sn__contains=search_q)|
                    Q(fw_rev__contains=search_q)|
                    Q(model__contains=search_q)|
                    Q(server_obj__manage_ip__contains=search_q)
                    )
        user_dict = request.session.get('is_login', None)
        if server_id: #从主机列表访问
            server_obj = Server.objects.get(id=server_id)
            queryset = Nvme_ssd.objects.filter(q_query,server_obj=server_obj)
        # if UserProfile.objects.get(name=user_dict['user']).is_admin :
        #     queryset = Nvme_ssd.objects.filter(node__contains=search_q)
        # else:
        #     queryset = Nvme_ssd.objects.filter(node__contains=search_q,
        #                                        server_obj__business_unit__roles__userprofile__name=user_dict['user'])
        else: #从ssd管理访问
            queryset = Nvme_ssd.objects.filter(q_query).order_by('server_obj__manage_ip')
        # 加载分页器
        queryset, page_html = init_paginaion(request, queryset)

        return render(request,'ssd.html',locals())

    elif request.method == "POST":
        query_set = Nvme_ssd.objects.all()
        ssd_list = [{'id':q.id,'ssd':'{0}-{1}-{2}-{3}-{4}'.format(q.server_obj.manage_ip,q.node,q.sn,q.model.split('-')[1],q.fw_rev)}
                    for q in query_set]
        return HttpResponse(json.dumps(ssd_list))


def ssd_smartlog(request):
    if request.method == "GET":
        step_time = request.GET.get("step_time","1800")  # 默认取30分钟内的smart_log
        if step_time.isdigit():
            step_time = int(step_time)
        ssd_id = request.GET.get("ssd_id",None)
        ssd_obj = Nvme_ssd.objects.get(id=ssd_id)

        limit_time = datetime.datetime.now() - datetime.timedelta(seconds=step_time)
        print(limit_time)
        query = Smart_log.objects.filter(ssd_obj=ssd_obj,log_date__gt=limit_time)
        if not query:
            result = {"code": 1, "message": "获取信息失败！"}
        else:
            result = {"code": 0, "message": "获取信息成功！"}

        return render(request,"ssd_smartlog.html",locals())