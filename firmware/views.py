from django.shortcuts import render,redirect,HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.http import FileResponse
from django.conf import settings
from firmware.models import *
from utils.md5 import match
import json
import copy
import time
import traceback
import os



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

        version_obj = FirmWareVerison.objects.get(id=version_id)
        device_obj = Device.objects.get(id=device_id)

        try:
            if image_file_obj:
                file_path = os.path.join(settings.BASE_DIR, 'firmware_image',
                                         version_obj.version_name,
                                         device_obj.device_name,
                                         image_type
                                         )
                if not os.path.exists(file_path):
                    os.makedirs(file_path)
                image_file = os.path.join(file_path, image_file_obj.name)
                f = open(image_file, 'wb')
                for c in image_file_obj.chunks():
                    f.write(c)
                f.close()

                file_md5 = match(image_file) #获取文件md5
                new_image_file = os.path.join(file_path,'%s_%s'%(image_file_obj.name,file_md5))
                os.rename(image_file,new_image_file) #重命名文件

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
            os.remove(img_obj.file_path)
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
            img_obj.update(download_url=download_url)
            result = {"code": 0, "message": "更新固件信息成功！"}
        except Exception as e:
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
            print(str(e))
            return HttpResponse('DownLoad Error!(%s)'%str(e))