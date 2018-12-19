from django.shortcuts import render,redirect,HttpResponseRedirect,HttpResponse
import json
# Create your views here.
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def version_info(request):
    if request.method == "GET":
        return render(request,'version_info.html')
    elif request.method == "POST":
        rep = [
            {'id':1,'name':'v1.1.0'},
            {'id':2,'name':'v1.2.0'},
            {'id':3,'name':'v1.3.0'},
            {'id':4,'name':'v1.4.0'},
            {'id':5,'name':'v1.5.0'},
            {'id':6,'name':'v1.6.0'},
            {'id': 1, 'name': 'v1.1.0'},
            {'id': 2, 'name': 'v1.2.0'},
            {'id': 3, 'name': 'v1.3.0'},
            {'id': 4, 'name': 'v1.4.0'},
            {'id': 5, 'name': 'v1.5.0'},
            {'id': 6, 'name': 'v1.6.0'},
            {'id': 1, 'name': 'v1.1.0'},
            {'id': 2, 'name': 'v1.2.0'},
            {'id': 3, 'name': 'v1.3.0'},
            {'id': 4, 'name': 'v1.4.0'},
            {'id': 5, 'name': 'v1.5.0'},
            {'id': 6, 'name': 'v1.6.0'},
        ]

        return HttpResponse(json.dumps(rep))

def get_device(request):
    if request.method == "GET":
        id = request.GET.get("id")
        # print(id)

        rep = [
            {'id': 1, 'name': '1T'},
            {'id': 2, 'name': '2T'},
            {'id': 3, 'name': '3T'},
            {'id': 4, 'name': '4T'},
            {'id': 5, 'name': '5T'},
            {'id': 6, 'name': '6T'},
        ]
        return HttpResponse(json.dumps(rep))

def get_image(request):
    if request.method == "GET":
        id = request.GET.get("id")
        # print(id)
        rep = [
            {'id': 1, 'image_type': 'boot','download_url':'image/boot','is_url':1,'enabled':1,'md5':''},
            {'id': 2, 'image_type': 'fwslot','download_url':'image/fwslot','is_url':0,'enabled':0,'md5':''},
            {'id': 3, 'image_type': 'drivecfg','download_url':'image/drivecfg','is_url':0,'enabled':0,'md5':''},
            {'id': 4, 'image_type': '55_drivecfg','download_url':'image/55_drivecfg','is_url':0,'enabled':1,'md5':''},
            {'id': 5, 'image_type': 'cc_drivecfg','download_url':'image/cc_drivecfg','is_url':0,'enabled':0,'md5':''},
            {'id': 6, 'image_type': 'conner','download_url':'image/conner','is_url':0,'enabled':1,'md5':''},
            {'id': 7, 'image_type': 'fwloader','download_url':'image/fwloader','is_url':0,'enabled':1,'md5':''},
        ]
        return HttpResponse(json.dumps(rep))





def image_enabled(request):
    if request.method == "POST":
        enabled = request.POST.get("enabled")
        image_id = request.POST.get("image_id")
        print(enabled,image_id)
        import time
        time.sleep(2)
        rep = {}
        return HttpResponse(json.dumps(rep))