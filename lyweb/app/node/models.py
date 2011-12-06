from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from lyweb import LuoYunConf as lyc


NETWORK_TYPE = (
    (0, 'UNKNOWN'),
    (1, 'Bridge'),
    (2, 'NAT'),
)

NODE_ARCH = (
    (0, 'UNKNOWN'),
    (1, '32 bit computer, x86'),
    (2, '64 bit computer, x86_64'),
)

NODE_STATUS = (
    (0, 'UNKNOWN'),
    (1, 'STOP'),
    (2, 'RUNNING'),
)

HYPERVISOR_TYPE = (
    (0, 'UNKNOWN'),
    (1, 'KVM'),
    (2, 'XEN'),
)


class Node(models.Model):

    hostname = models.CharField('Node hostname', max_length = 30)
    ip = models.CharField('Node IP', max_length = 32)
    port = models.IntegerField('Port', default = lyc.LY_NODE_DEFAULT_PORT)
    arch = models.IntegerField('Node Arch', default = 0, choices = NODE_ARCH)
    status = models.IntegerField('Node Status', default = 0, choices = NODE_STATUS)

    hypervisor = models.IntegerField('Hypervisor', default = 0, choices = HYPERVISOR_TYPE)
    hypervisor_version = models.IntegerField('Hypervisor Version', null = True, blank = True)
    libversion = models.IntegerField('Version of libvirt', null = True, blank = True)

    network_type = models.IntegerField('Network type', default = 0, choices = NETWORK_TYPE)

    # Resources
    max_memory = models.IntegerField('Max Memory', null = True)
    max_cpus = models.IntegerField('Max CPUs', default = 1, null = True)
    cpu_model = models.CharField('CPU model', max_length = 32, null = True)
    cpu_mhz = models.IntegerField('CPU frequency', default = 0, null = True)

    # dynamic
    load_average = models.IntegerField('Load Average', null = True) # x 100
    free_memory = models.IntegerField('Free Memory', null = True)

    created = models.DateTimeField('Created', auto_now_add = True)
    updated = models.DateTimeField('Updated', auto_now = True)


    class Meta:
        ordering = ['-updated']
        db_table = 'node'
        verbose_name = 'Node'
        verbose_name_plural = 'Node'
