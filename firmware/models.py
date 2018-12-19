from django.db import models

# Create your models here.
class FirmWareVerison(models.Model):
    """

    """
    version_number = models.CharField('版本号', max_length=32)
    # is_admin = models.BooleanField(default=False)
    # ssd_obj = models.ForeignKey(to="cmdb.Nvme_ssd",related_name="")
    class Meta:
        verbose_name_plural = "固件版本表"

    def __str__(self):
        return self.version_number

class Device(models.Model):
    """

    """
    name = models.CharField('产品名称',max_length=32)
    firmware = models.ForeignKey('对应固件版本', to='FirmWareVerison')

class Image(models.Model):
    """

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
    device = models.ForeignKey('对应产品',to='Device')
    is_url = models.BooleanField(default=True)
    enabled = models.BooleanField(default=False)
    md5 = models.CharField(max_length=64,null=True,blank=True)
