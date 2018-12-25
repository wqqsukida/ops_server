#!/usr/bin/env python
# -*- coding:utf-8 -*-
#----------------------------------------------
#@version:    ??                               
#@author:   Dylan_wu                                                        
#@software:    PyCharm                  
#@file:    md5.py
#@time:    2017/9/4 9:39
#----------------------------------------------
import hashlib

def encrypt(pwd):
    obj = hashlib.md5()
    obj.update(pwd.encode('utf-8'))
    res = obj.hexdigest()
    return res

def match(file_path,Bytes=1024):
    md5_1 = hashlib.md5()                        #创建一个md5算法对象
    with open(file_path,'rb') as f:              #打开一个文件，必须是'rb'模式打开
        while 1:
            data =f.read(Bytes)                  #由于是一个文件，每次只读取固定字节
            if data:                     #当读取内容不为空时对读取内容进行update
                md5_1.update(data)
            else:                        #当整个文件读完之后停止update
                break
    ret = md5_1.hexdigest()              #获取这个文件的MD5值
    return ret