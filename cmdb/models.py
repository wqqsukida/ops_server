from django.db import models

# Create your models here.
from rbac import models  as rbac_model


class BusinessUnit(models.Model):
    """
    主机组(部门)
    """
    name = models.CharField(verbose_name='主机组名称', max_length=64, unique=True) # 销售，1,2
    roles = models.ManyToManyField(verbose_name="对应用户组",to=rbac_model.Role,blank=True) # 运维管理人员：2

    class Meta:
        verbose_name_plural = "主机组表"

    def __str__(self):
        return self.name

class Tag(models.Model):
    """
    资产标签
    """
    name = models.CharField('标签', max_length=32, unique=True)

    class Meta:
        verbose_name_plural = "标签表"

    def __str__(self):
        return self.name

class IDC(models.Model):
    """
    机房信息
    """
    name = models.CharField('机房', max_length=32)
    floor = models.IntegerField('楼层', default=1)

    class Meta:
        verbose_name_plural = "机房表"

    def __str__(self):
        return self.name



class Server(models.Model):
    """
    服务器信息
    """
    # asset = models.OneToOneField('Asset')

    cert_id = models.CharField('唯一ID',max_length=64,unique=True)
    comment = models.CharField('备注信息',max_length=32,null=True,blank=True)
    idc = models.ForeignKey(IDC,null=True, blank=True)
    cabinet_num = models.CharField('机柜号', max_length=30, null=True, blank=True)
    cabinet_order = models.CharField('机柜中序号', max_length=30, null=True, blank=True)

    business_unit = models.ManyToManyField(to=BusinessUnit, blank=True)

    tags = models.ManyToManyField(Tag)


    server_status_choices = (
        (1, '上架'),
        (2, '在线'),
        (3, '离线'),
        (4, '下架'),
    )

    server_status_id = models.IntegerField(choices=server_status_choices, default=1)

    hostname = models.CharField(max_length=128,null=True,blank=True)
    nickname = models.CharField('主机别名',max_length=128,null=True,blank=True)
    sn = models.CharField('SN号', max_length=128, db_index=True)
    manufacturer = models.CharField(verbose_name='制造商', max_length=64, null=True, blank=True)
    model = models.CharField('型号', max_length=64, null=True, blank=True)

    manage_ip = models.GenericIPAddressField('管理IP', null=True, blank=True)

    os_platform = models.CharField('系统', max_length=128, null=True, blank=True)
    os_version = models.CharField('系统版本', max_length=128, null=True, blank=True)

    cpu_count = models.IntegerField('CPU个数', null=True, blank=True)
    cpu_physical_count = models.IntegerField('CPU物理个数', null=True, blank=True)
    cpu_model = models.CharField('CPU型号', max_length=128, null=True, blank=True)

    create_at = models.DateTimeField(auto_now_add=True, blank=True)

    latest_date = models.DateTimeField(null=True,blank=True)
    client_version = models.CharField('客户端版本',max_length=32,null=True,blank=True)
    def run_task_count(self):
        return self.server_task.name

    class Meta:
        verbose_name_plural = "服务器表"

    def __str__(self):
        return self.manage_ip




class Disk(models.Model):
    """
    硬盘信息
    """
    slot = models.CharField('插槽位', max_length=8)
    model = models.CharField('磁盘型号', max_length=256)
    capacity = models.FloatField('磁盘容量GB')
    pd_type = models.CharField('磁盘类型', max_length=256)
    server_obj = models.ForeignKey('Server',related_name='disk')

    class Meta:
        verbose_name_plural = "硬盘表"

    def __str__(self):
        return self.slot

class Nvme_ssd(models.Model):
    """
    Nvme_ssd
    """
    node = models.CharField('',max_length=64)
    sn = models.CharField('SN号', max_length=128,null=True,unique=True)
    model = models.CharField('SSD型号', max_length=256,null=True)
    namespace = models.CharField('', max_length=32,null=True)
    capacity = models.CharField('設備容量', max_length=128,null=True)
    format = models.CharField('', max_length=128,null=True)
    fw_rev = models.CharField('', max_length=64,null=True)
    server_obj = models.ForeignKey('Server', related_name='nvme_ssd')

    class Meta:
        verbose_name_plural = "SSD表"

    def __str__(self):
        return self.node

class Smart_log(models.Model):
    """
    ssd smart_log
    """
    critical_warning = models.CharField(max_length=128, null=True)
    temperature = models.CharField(max_length=128, null=True)
    available_spare = models.CharField(max_length=128, null=True)
    available_spare_threshold = models.CharField(max_length=128, null=True)
    percentage_used = models.CharField(max_length=128, null=True)
    data_units_read = models.CharField(max_length=128, null=True)
    data_units_written = models.CharField(max_length=128, null=True)
    host_read_commands = models.CharField(max_length=128, null=True)
    host_write_commands = models.CharField(max_length=128, null=True)
    controller_busy_time = models.CharField(max_length=128, null=True)
    power_cycles = models.CharField(max_length=128, null=True)
    power_on_hours = models.CharField(max_length=128, null=True)
    unsafe_shutdowns = models.CharField(max_length=128, null=True)
    media_errors = models.CharField(max_length=128, null=True)
    num_err_log_entries = models.CharField(max_length=128, null=True)

    warning_temperature_time = models.CharField(max_length=128, null=True)
    critical_composite_temperature_time = models.CharField(max_length=128, null=True)

    temperature_sensor1 = models.CharField(max_length=128, null=True)
    temperature_sensor2 = models.CharField(max_length=128, null=True)
    temperature_sensor3 = models.CharField(max_length=128, null=True)
    temperature_sensor4 = models.CharField(max_length=128, null=True)

    thermal_management_t1_trans_count = models.CharField(max_length=128, null=True)
    thermal_management_t2_trans_count = models.CharField(max_length=128, null=True)

    thermal_management_t1_total_time = models.CharField(max_length=128, null=True)
    thermal_management_t2_total_time = models.CharField(max_length=128, null=True)

    ssd_obj = models.ForeignKey(to='Nvme_ssd',related_name='smart_log')
    log_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "SmartLog表"


class NIC(models.Model):
    """
    网卡信息
    """
    name = models.CharField('网卡名称', max_length=128)
    hwaddr = models.CharField('网卡mac地址', max_length=64)
    netmask = models.CharField(max_length=64)
    ipaddrs = models.CharField('ip地址', max_length=256)
    up = models.BooleanField(default=False)
    server_obj = models.ForeignKey('Server',related_name='nic')


    class Meta:
        verbose_name_plural = "网卡表"

    def __str__(self):
        return self.name


class Memory(models.Model):
    """
    内存信息
    """
    slot = models.CharField('插槽位', max_length=32)
    manufacturer = models.CharField('制造商', max_length=32, null=True, blank=True)
    model = models.CharField('型号', max_length=64)
    capacity = models.FloatField('容量', null=True, blank=True)
    sn = models.CharField('内存SN号', max_length=64, null=True, blank=True)
    speed = models.CharField('速度', max_length=16, null=True, blank=True)

    server_obj = models.ForeignKey('Server',related_name='memory')


    class Meta:
        verbose_name_plural = "内存表"

    def __str__(self):
        return self.slot


class ServerRecord(models.Model):
    """
    服务器变更记录,creator为空时，表示是资产汇报的数据。
    """
    server_obj = models.ForeignKey('Server', related_name='ar')
    content = models.TextField(null=True)
    creator = models.ForeignKey(to=rbac_model.UserProfile, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "资产记录表"

    def __str__(self):
        return self.server_obj.hostname

class FocusTask(models.Model):
    '''

    '''
    server_obj = models.OneToOneField(to='Server',related_name='server_focus_task')
    name = models.CharField('任务名',max_length=64,null=True,blank=True)
    args = models.CharField('任务参数',max_length=128,null=True,blank=True)
    path = models.CharField('路径',max_length=256,null=True,blank=True)
    status = models.IntegerField('任务状态',default='0',null=True,blank=True)
    msg = models.TextField('任务信息',null=True,blank=True)
    elapsed = models.CharField('执行时间',max_length=32,null=True,blank=True)
