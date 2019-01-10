from django.db import models

# Create your models here.
class FirmWareVerison(models.Model):
    """
    版本表
    """
    version_name = models.CharField('版本号', max_length=32,unique=True)

    class Meta:
        verbose_name_plural = "版本表"

    def __str__(self):
        return self.version_name

class Device(models.Model):
    """
    产品类型
    """
    device_name = models.CharField('产品类型名称',max_length=32)
    version = models.ForeignKey(to='FirmWareVerison')

    class Meta:
        unique_together = ('device_name', 'version',)

class Image(models.Model):
    """
    image表
    """
    image_type_choices = (
        (1, 'boot'),
        (2, 'fwslot'),
        (3, 'drivecfg'),
        (4, '55_drivecfg'),
        (5, 'cc_drivecfg'),
        (6, 'conner'),
        (7, 'fwloader'),
    )

    image_type = models.IntegerField(choices=image_type_choices, default=1)
    download_url = models.CharField('下载地址',max_length=256,null=True,blank=True)
    file_path = models.CharField('存放路径',max_length=256,null=True,blank=True)
    device = models.ForeignKey(to='Device')
    is_url = models.BooleanField(default=True)
    enabled = models.BooleanField(default=False)
    md5 = models.CharField(max_length=64,null=True,blank=True)

    class Meta:
        unique_together = ('image_type', 'device',)

class Update_task(models.Model):
    """

    """
    ssd_obj = models.ForeignKey(to='cmdb.Nvme_ssd',related_name='update_task')
    img_obj = models.ForeignKey(to='Image',related_name='update_task')
    task_status_choices = (
        (1, '新建'),
        (2, '执行完成'),
        (3, '执行错误'),
        (4, '执行暂停'),
        (5, '执行中')
    )
    status = models.IntegerField('状态',choices=task_status_choices,default='1')
    update_res = models.TextField('任务结果', null=True, blank=True)
    create_date = models.DateTimeField('创建时间',auto_now_add=True)
    finished_date = models.DateTimeField('完成时间',null=True,blank=True)
    run_time = models.CharField('总计时间',max_length=32,null=True,blank=True)
