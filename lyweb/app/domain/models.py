from django.utils.translation import ugettext as _

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

NETWORK_TYPE = (
    (0, 'UNKNOWN'),
    (1, 'STATIC'),
    (2, 'DHCP'),
)


class AppCatalog(models.Model):

    '''
    What's the catalog of domain
    '''
    name = models.CharField(_('Catalog Name'), blank=False, max_length = 64, unique = True)
    summary = models.CharField(_('Summary'), max_length=128)
    description = models.TextField(_('Description about the image'), blank=True,  default='')

    user = models.ForeignKey(User, related_name = 'user_domains', verbose_name = 'User')
    position = models.IntegerField(_('Position'), blank=True, default=0, help_text=_('Position catalog sequence'))

    created = models.DateTimeField(_('Created Time'), auto_now_add = True)
    updated = models.DateTimeField(_('Updated Time'), auto_now = True)

    class Meta:
        ordering = ['-updated']
        db_table = 'app_catalog'

    def __unicode__(self):
        return self.name



class Domain(models.Model):

    name = models.CharField(_('Name'), max_length = 32)
    summary = models.CharField(_('Summary'), max_length=128)
    description = models.TextField(_('Description'), blank = True, default = '')

    cpus = models.IntegerField(_('CPUs'), default = 1, blank = True)
    memory = models.IntegerField(_('Memory size'), default = 0, blank = True)

    user = models.ForeignKey(User, verbose_name = 'User')
    catalog = models.ForeignKey(AppCatalog, verbose_name = 'AppCatalog', blank = True, null = True)

    image = models.ForeignKey(Image, related_name = 'image_domains', verbose_name = 'Disk Image', blank = True)
    node = models.ForeignKey(Node, related_name = 'node_domains', verbose_name = 'Node', blank = True, null = True)

    # Network for cloud control, sometimes it's just the only network
    network = models.IntegerField(_('Network Type'), default = 0, choices = NETWORK_TYPE)
    ip = models.CharField(_('IP'), max_length = 32, blank = True, null = True)
    netmask = models.CharField(_('Netmask'), max_length = 32, blank = True, null = True)
    gateway = models.CharField(_('Gateway'), max_length = 32, blank = True, null = True)
    mac = models.CharField(_('MAC'), max_length = 32, blank = True, null = True)

    # Config path, save user, network, storage, other devices information
    config = models.CharField(_('Config File'), max_length=256, default = "")

    status = models.IntegerField(_('Status'), default = 0, choices = DOMAIN_STATUS)

    created = models.DateTimeField(_('Created'), auto_now_add = True)
    updated = models.DateTimeField(_('Updated'), auto_now = True)

    class Meta:
        ordering = ['-updated']
        db_table = 'domain'
        verbose_name = _('Domain')
        verbose_name_plural = _('Domain')

    def __unicode__(self):
        return self.name
