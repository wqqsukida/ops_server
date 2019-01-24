from django.shortcuts import render,redirect,HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.http import FileResponse
from django.conf import settings
from firmware.models import *
from cmdb.models import Server,Nvme_ssd
from utils.md5 import match
import json
import copy
import time
import traceback
import os
from utils.ansible_api import Runner
from utils.pagination import Pagination

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

@csrf_exempt
def version_info(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}
        return render(request,'version_info.html',locals())

    elif request.method == "POST":
        query_set = FirmWareVerison.objects.all()
        rep = [model_to_dict(q) for q in query_set]
        return HttpResponse(json.dumps(rep))

def version_add(request):
    if request.method == "POST":
        version_name = request.POST.get("version_name")
        if version_name:
            try:
                FirmWareVerison.objects.create(version_name=version_name)
                result = {"code": 0, "message": "添加版本成功！"}
            except Exception as e:
                result = {"code": 1, "message": e}
        else:
            result = {"code": 1, "message": "版本名不能为空！"}
        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def version_del(request):
    if request.method == "GET":
        id = request.GET.get("vid",None)
        try:
            FirmWareVerison.objects.get(id=id).delete()
            result = {"code": 0, "message": "删除版本成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def version_edit(request):
    if request.method == "POST":
        id = request.POST.get("id",None)
        version_name = request.POST.get("version_name",None)
        try:
            ver_obj = FirmWareVerison.objects.filter(id=id)
            ver_obj.update(version_name=version_name)
            result = {"code": 0, "message": "更新版本成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))
def dev_list(request):
    if request.method == "GET":
        id = request.GET.get("version_id")
        query_set = Device.objects.filter(version=id)
        rep = [model_to_dict(q) for q in query_set]

        return HttpResponse(json.dumps(rep))

def dev_add(request):
    if request.method == "POST":
        device_name = request.POST.get("device_name")
        version_id = request.POST.get("version_id")
        if device_name:
            try:
                Device.objects.create(device_name=device_name,version_id=version_id)
                result = {"code": 0, "message": "添加产品类型成功！"}
            except Exception as e:
                result = {"code": 1, "message": e}
        else:
            result = {"code": 1, "message": "产品名称不能为空！"}
        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def dev_del(request):
    if request.method == "GET":
        id = request.GET.get("did",None)
        try:
            Device.objects.get(id=id).delete()
            result = {"code": 0, "message": "删除产品类型成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def dev_edit(request):
    if request.method == "POST":
        id = request.POST.get("id",None)
        device_name = request.POST.get("device_name",None)
        try:
            dev_obj = Device.objects.filter(id=id)
            dev_obj.update(device_name=device_name)
            result = {"code": 0, "message": "更新产品类型成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def img_list(request):
    if request.method == "GET":
        id = request.GET.get("device_id")
        query_set = Image.objects.filter(device=id)
        rep = []
        for q in query_set:
            q_dict = model_to_dict(q)
            q_dict['image_name'] = q.get_image_type_display()
            rep.append(q_dict)
        # rep = [model_to_dict(q) for q in query_set]
        return HttpResponse(json.dumps(rep))

    elif request.method == "POST":
        id = request.POST.get("device_id")
        query_set = Image.objects.filter(device=id)
        image_choices = list(copy.deepcopy(Image.image_type_choices))
        for q in query_set:
            if (q.image_type,q.get_image_type_display()) in image_choices:
                image_choices.remove((q.image_type,q.get_image_type_display()))

        return HttpResponse(json.dumps(image_choices))

def img_add(request):
    if request.method == "POST":
        version_id = request.POST.get("version_id",None)
        device_id = request.POST.get("device_id",None)
        image_type = request.POST.get("image_type",None)
        download_url = request.POST.get("download_url",None)
        image_file_obj = request.FILES.get("image_file")

        version_obj = FirmWareVerison.objects.filter(id=version_id).first()
        device_obj = Device.objects.filter(id=device_id).first()

        try:
            if image_file_obj:
                # 1.拼接新文件路径
                file_path = os.path.join(settings.BASE_DIR, 'firmware_image',
                                         version_obj.version_name,
                                         device_obj.device_name,
                                         image_type
                                         )
                if not os.path.exists(file_path):
                    os.makedirs(file_path)
                image_file = os.path.join(file_path, image_file_obj.name)
                # 2.创建新文件
                f = open(image_file, 'wb')
                for c in image_file_obj.chunks():
                    f.write(c)
                f.close()
                # 3.获取文件md5并重命名
                file_md5 = match(image_file)
                new_image_file = os.path.join(file_path,'%s_%s'%(image_file_obj.name,file_md5))
                os.rename(image_file,new_image_file) #重命名文件
                # 4.数据库添加
                download_url = 'http://10.0.2.20/firmware/image_download/?fid={0}'.format(file_md5)
                Image.objects.create(device=device_obj,image_type=image_type,download_url=download_url,
                                     md5=file_md5,file_path=new_image_file,is_url=False)
            else:
                Image.objects.create(device=device_obj,image_type=image_type,
                                     download_url=download_url)
            result = {"code": 0, "message": "添加固件成功！"}
        except Exception as e:
            print(traceback.format_exc())
            result = {"code": 1, "message": e}

        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def img_del(request):
    if request.method == "GET":
        id = request.GET.get("imid",None)
        try:
            img_obj = Image.objects.get(id=id)
            if img_obj.file_path:
                os.remove(img_obj.file_path) #删除对应本地image
            img_obj.delete()
            result = {"code": 0, "message": "删除固件类型成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def img_edit(request):
    if request.method == "POST":
        id = request.POST.get("id",None)
        download_url = request.POST.get("download_url", None)
        image_file_obj = request.FILES.get("image_file")
        try:
            img_obj = Image.objects.filter(id=id)
            if image_file_obj:
                # 1.删除原文件
                old_file = img_obj.first().file_path
                if old_file and os.path.exists(old_file):
                    os.remove(old_file)
                # 2.拼接新文件路径
                new_file_path = os.path.join(settings.BASE_DIR, 'firmware_image',
                                         img_obj.first().device.version.version_name,
                                         img_obj.first().device.device_name,
                                         str(img_obj.first().image_type),
                                         )
                if not os.path.exists(new_file_path):
                    os.makedirs(new_file_path)
                image_file = os.path.join(new_file_path, image_file_obj.name)
                # 3.创建新文件
                f = open(image_file, 'wb')
                for c in image_file_obj.chunks():
                    f.write(c)
                f.close()
                # 4.获取文件md5并重命名
                file_md5 = match(image_file)
                new_image_file = os.path.join(new_file_path,'%s_%s'%(image_file_obj.name,file_md5))
                os.rename(image_file,new_image_file)
                # 5.更新数据库
                download_url = 'http://10.0.2.20/firmware/image_download/?fid={0}'.format(file_md5)
                img_obj.update(download_url=download_url,file_path=new_image_file,is_url=False,
                               md5=file_md5)
                result = {"code": 0, "message": "替换image成功！"}
            else:

                img_obj.update(download_url=download_url)
                result = {"code": 0, "message": "更新固件url成功！"}
        except Exception as e:
            print(traceback.format_exc())
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/firmware/version_info?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def img_enabled(request):
    if request.method == "POST":
        enabled = request.POST.get("enabled")
        image_id = request.POST.get("image_id")

        # print (image_id,enabled)
        try:
            Image.objects.filter(id=image_id).update(enabled=enabled)
            rep = {'code':1}
        except Exception as e:
            rep = {'code':0}
        return HttpResponse(json.dumps(rep))

def image_download(request):
    if request.method == "GET":
        fid = request.GET.get("fid")
        try:
            image_obj = Image.objects.filter(md5=fid).first()
            file_path = image_obj.file_path
            file_name = file_path.rsplit('/',1)[-1]
            file = open(file_path,'rb')
            rep = FileResponse(file)
            rep['Content-type'] = 'application/octet-stream'
            rep['Content-Disposition'] = 'attachment;filename=%s'%file_name
            return rep
        except Exception as e:
            print(traceback.format_exc())
            return HttpResponse('DownLoad Error!(%s)'%str(e))

#===================================================================================
def version_update(request):
    if request.method == "GET":

        return render(request,'version_update.html',locals())

def ssd_update(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        versions = FirmWareVerison.objects.all()
        choices = Image.image_type_choices
        ssd = Nvme_ssd.objects.all()
        return render(request,'ssd_update.html',locals())
    elif request.method == "POST":
        result = {}
        ver_id = request.POST.get("fw_ver")
        img_type_id = request.POST.get("img_type")
        ssd_list = request.POST.getlist("ssd_list")
        if ssd_list:
            try:
                res_msg = []
                for sid in ssd_list:
                    ssd_obj = Nvme_ssd.objects.get(id=sid)
                    ssd_model = ssd_obj.model.split('-')[1]
                    img_obj = Image.objects.filter(
                        device__version_id=ver_id,
                        device__device_name=ssd_model,
                        image_type=img_type_id,
                        enabled=1
                    ).first()
                    if img_obj:
                        Update_task.objects.create(ssd_obj=ssd_obj,img_obj=img_obj)
                    else:
                        res_msg.append('对应设备{0}-{1}的image不存在或者不可用！'.format(ssd_model,ssd_obj.sn))
                if res_msg:
                    result = {"code": 2, "message":str(res_msg)}
                else:
                    result = {"code": 0, "message": "升级提交成功"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "请至少选择一个要升级的设备！"}

        return HttpResponseRedirect('/firmware/ssd_update?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def host_update(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        versions = FirmWareVerison.objects.all()
        choices = Image.image_type_choices
        hosts = Server.objects.all()
        return render(request,'host_update.html',locals())
    elif request.method == "POST":
        result = {}
        ver_id = request.POST.get("fw_ver")
        img_type_id = request.POST.get("img_type")
        host_list = request.POST.getlist("host_list")
        if host_list:
            try:
                res_msg = []
                for hid in host_list:
                    server_obj = Server.objects.get(id=hid)
                    server_ssds_query = Nvme_ssd.objects.filter(server_obj=server_obj)
                    for ssd_obj in server_ssds_query:
                        ssd_model = ssd_obj.model.split('-')[1]
                        # ver_obj = FirmWareVerison.objects.get(id=ver_id)
                        # dev_obj = Device.objects.filter(version=ver_id,device_name=ssd_model).first()
                        img_obj = Image.objects.filter(
                            device__version_id=ver_id,
                            device__device_name=ssd_model,
                            image_type=img_type_id,
                            enabled=1,
                        ).first()
                        if img_obj:
                            Update_task.objects.create(ssd_obj=ssd_obj,img_obj=img_obj)
                        else:
                            res_msg.append('对应设备{0}-{1}-{2}的image不存在或者不可用！'.format(
                                server_obj.manage_ip,
                                ssd_model,ssd_obj.sn)
                            )
                if res_msg:
                    result = {"code": 2, "message":str(res_msg)}
                else:
                    result = {"code": 0, "message": "升级提交成功！"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "请至少选择一个要升级设备的主机！"}

        return HttpResponseRedirect('/firmware/host_update?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                ))

def update_history(request):
    if request.method == "GET":
        queryset = Update_task.objects.all().order_by('-create_date')
        task_list, page_html = init_paginaion(request, queryset)
        return render(request,'update_history.html',locals())
    elif request.method == "POST":
        id = request.POST.get("task_id")
        img_obj = Update_task.objects.get(id=id)
        u_res = '升级执行中...'
        res = img_obj.update_res
        if res:
            u_res = res

        return HttpResponse(json.dumps(u_res))
#===================================================================================
def client_update(request):
    '''
    客户端升级
    :param request:
    :return:
    '''
    if request.method == "POST" :
        result = {"code":0,"message":"test"}
        hosts = request.POST.getlist("hosts")
        if hosts:
            hosts = ','.join(hosts)+','
        ansible_client = Runner(hosts)
        ansible_client.run_playbook()
        msg = ansible_client.get_playbook_result()

        return HttpResponse(json.dumps(msg))


    elif request.method == "GET" :
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        # host_query = Server.objects.filter(server_status_id=2)

        return render(request,'client_update.html',locals())

    elif request.method == "PUT" :
        query_set = Server.objects.filter(server_status_id=2)
        data = [{"ip":q.manage_ip,"client_ver":"{0}-{1}-{2}".
            format(q.manage_ip,q.hostname,q.client_version)} for q in query_set]

        return HttpResponse(json.dumps(data))