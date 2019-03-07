from django.db import models

# Create your models here.

class TaskMethod(models.Model):
    '''
    主机任务模板
    '''
    title = models.CharField('模板名称', max_length=32,unique=True)
    run_path = models.CharField('任务执行路径',max_length=256,default='/tmp/test.py')
    args = models.CharField('任务参数',max_length=64,null=True,blank=True)
    content = models.TextField('任务描述',null=True,blank=True)
    create_date = models.DateTimeField('模板创建时间', auto_now_add=True)
    # has_file = models.BooleanField(default=False)
    # file_url = models.CharField('客户端生成文件路径', max_length=256,null=True,blank=True)
    task_script = models.ForeignKey(to='TaskScript')

class TaskScript(models.Model):
    '''
    任务脚本表
    '''
    name = models.CharField('脚本名称', max_length=64,unique=True)
    script_path = models.CharField('脚本路径', max_length=256)
    download_url = models.CharField('下载地址', max_length=256)

class ServerTask(models.Model):
    '''

    '''
    server_obj = models.ForeignKey(to='cmdb.Server',related_name='server_task')
    task_obj = models.ForeignKey(to='TaskMethod')
    session_obj = models.ForeignKey(to='TaskSession', null=True, blank=True)
    # name = models.CharField('任务名',max_length=64,null=True,blank=True)
    # args = models.CharField('任务参数',max_length=128,null=True,blank=True)
    # path = models.CharField('路径',max_length=256,null=True,blank=True)
    task_status_choices = (
        (1, 'NEW'),
        (2, 'FINISH'),
        (3, 'ERROR'),
        (4, 'PAUSE'),
        (5, 'RUNNING')
    )
    status = models.IntegerField('任务状态',choices=task_status_choices,default='1',null=True,blank=True)
    msg = models.TextField('任务信息',null=True,blank=True)
    elapsed = models.CharField('执行时间',max_length=32,null=True,blank=True)
    create_date = models.DateTimeField('任务创建时间',auto_now_add=True)
    finished_date = models.DateTimeField('任务完成时间', null=True, blank=True)

class TaskSession(models.Model):
    '''
    主机任务会话表
    '''
    title = models.CharField('会话名称', max_length=32,null=False,blank=False)
    server_obj = models.ManyToManyField(to='cmdb.Server')
    task_obj = models.ManyToManyField(to='TaskMethod')
    content = models.TextField('会话描述',null=True,blank=True)
    create_date = models.DateTimeField('会话创建时间', auto_now_add=True)
    is_random = models.BooleanField('是否随机执行',default=False)

    def ast(self):
        return self.servertask_set.count()

    def nst(self):
        return self.servertask_set.filter(status=1).count()

    def fst(self):
        return self.servertask_set.filter(status=2).count()

    def est(self):
        return self.servertask_set.filter(status=3).count()

    def pst(self):
        return self.servertask_set.filter(status=4).count()

    def rst(self):
        return self.servertask_set.filter(status=5).count()