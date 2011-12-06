from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import User
from lyweb import LuoYunConf as lyc
from lyweb.app.image.models import Image
from lyweb.app.node.models import Node

DOMAIN_STATUS = (
    (0, 'UNKNOWN'),
    (1, 'STOP'),
    (2, 'RUNNING'),
    (3, 'SUSPEND'),
    (4, 'MIGERATE'),
)


class Domain(models.Model):

    name = models.CharField('Domain Name', max_length = 32)
    uuid = models.CharField('Domain UUID', max_length = 64, blank = True)
    description = models.TextField('Description', blank = True, default = '')
    node = models.ForeignKey(Node, related_name = 'node_domains', verbose_name = 'Node', blank = True, null = True)
    user = models.ForeignKey(User, related_name = 'user_domains', verbose_name = 'User')

    diskimg = models.ForeignKey(Image, related_name = 'diskimg_domains', verbose_name = 'Disk Image', blank = True)
    kernel = models.ForeignKey(Image, related_name = 'kernel_domains', verbose_name = 'Kernel Image', blank = True, null = True)
    initrd = models.ForeignKey(Image, related_name = 'initrd_domains', verbose_name = 'Initrd Image', blank = True, null = True)
    #Fixed me: need storage, network, device(usb, pci, input, ...) Object
    #network = models.ManyToManyField(Network, related_name = 'network_domains', verbose_name = 'Network', blank = True)

    # The first network should be list here, others can used
    # as addons.
    ip = models.CharField('Domain IP', max_length = 32, 
                          blank = True, null = True)
    mac = models.CharField('Domain MAC', max_length = 32,
                           blank = True, null = True)

    # boot order : disk , cd , network etc.
    boot = models.CharField('Boot order', max_length = 128, default = 'cd, disk')
    cpus = models.IntegerField('CPUs', default = 1, blank = True)
    memory = models.IntegerField('Memory size', default = 0, blank = True)

    status = models.IntegerField('Domain Status', default = 0, choices = DOMAIN_STATUS)

    created = models.DateTimeField('Created', auto_now_add = True)
    updated = models.DateTimeField('Updated', auto_now = True)

    class Meta:
        ordering = ['-updated']
        db_table = 'domain'
        verbose_name = 'Domain'
        verbose_name_plural = 'Domain'
