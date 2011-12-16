from django.utils.translation import ugettext as _

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from lyweb import LuoYunConf as lyc


NETWORK_TYPE = (
    (0, _('UNKNOWN')),
    (1, _('Bridge')),
    (2, _('NAT')),
)

NODE_ARCH = (
    (0, _('UNKNOWN')),
    (1, _('32 bit computer, x86')),
    (2, _('64 bit computer, x86_64')),
)

NODE_STATUS = (
    (0, _('UNKNOWN')),
    (1, _('STOP')),
    (2, _('RUNNING')),
)

HYPERVISOR_TYPE = (
    (0, _('UNKNOWN')),
    (1, _('KVM')),
    (2, _('XEN')),
)


class Node(models.Model):

    hostname = models.CharField(_('Hostname'), max_length = 30)

    arch = models.IntegerField(_('Arch'), default = 0, choices = NODE_ARCH)
    status = models.IntegerField(_('Status'), default = 0, choices = NODE_STATUS)

    # control network
    ip = models.CharField(_('IP'), max_length = 32)
    port = models.IntegerField(_('Port'), default = lyc.LY_NODE_DEFAULT_PORT)


    hypervisor = models.IntegerField(_('Hypervisor'), default = 0, choices = HYPERVISOR_TYPE)
    #hypervisor_version = models.IntegerField('Hypervisor Version', null = True, blank = True)
    #libversion = models.IntegerField('Version of libvirt', null = True, blank = True)

    network_type = models.IntegerField(_('Network type'), default = 0, choices = NETWORK_TYPE)

    # Resources
    max_memory = models.IntegerField(_('Max Memory'), null = True)
    max_cpus = models.IntegerField(_('Max CPUs'), default = 1, null = True)
    cpu_model = models.CharField(_('CPU model'), max_length = 32, null = True)
    cpu_mhz = models.IntegerField(_('CPU frequency'), default = 0, null = True)

    # dynamic
    load_average = models.IntegerField(_('Load Average'), null = True) # x 100
    free_memory = models.IntegerField(_('Free Memory'), null = True)

    # Config path, extend sometimes
    config = models.CharField(_('Config File'), max_length=256, default = "")

    created = models.DateTimeField(_('Created'), auto_now_add = True)
    updated = models.DateTimeField(_('Updated'), auto_now = True)


    class Meta:
        ordering = ['-updated']
        db_table = 'node'
        verbose_name = _('Node')
        verbose_name_plural = _('Node')


    def __unicode__(self):
        return self.hostname
