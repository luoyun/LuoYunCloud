from django.utils.translation import ugettext as _

import os, hashlib
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from lyweb import LuoYunConf as lyc

IMAGE_TYPE = ( 
    (0, _('UNKNOWN')),
    (1, _('Kernel')),
    (2, _('Ramdisk')),
    (3, _('Raw Disk')),
    (4, _('ISO')),
)

IMAGE_STATUS = ( 
    (0, _('UNKNOWN')),
    (1, _('OK')),
    (2, _('NOT COMPLETE')),
    (3, _('LOCK')),
)


RESOURCE_PROTOCOL = ( 
    (0, _('UNKNOWN')),
    (1, _('Filesystem')),
)

CHECKSUM_TYPE = (
    (1, _('MD5')),
    (2, _('SHA1')),
)


class ImageCatalog(models.Model):
    '''
    What's the catalog of image
    '''
    name = models.CharField(_('Catalog Name'), blank=False, max_length = 64, unique = True)
    summary = models.CharField(_('Summary'), max_length=128)
    description = models.TextField(_('Description about the image'), blank=True,  default='')

    position = models.IntegerField(_('Position'), blank=True, default=0, help_text=_('Position catalog sequence'))

    created = models.DateTimeField(_('Created Time'), auto_now_add = True)
    updated = models.DateTimeField(_('Updated Time'), auto_now = True)

    class Meta:
        ordering = ['-updated']
        db_table = 'image_catalog'

    def __unicode__(self):
        return self.name


class ImageOriginInfo(models.Model):
    '''
    Information about the origination of the image.
    '''
    name = models.CharField(_('Origination Nmae'), max_length = 64, blank = True)
    home = models.CharField(_('Home Page'), max_length = 128, blank = True)
    summary = models.CharField(_('Summary'), max_length=128)
    description = models.TextField(_('Description about the image'), blank=True,  default='')

    created = models.DateTimeField(_('Created Time'), auto_now_add = True)
    updated = models.DateTimeField(_('Updated Time'), auto_now = True)

    class Meta:
        ordering = ['-updated']
        db_table = 'image_origin'

    def __unicode__(self):
        return self.name



class Image(models.Model):
    '''
    Information about the image.
    '''

    name = models.CharField(_('Image Name'), max_length = 30, blank = True, unique = True)
    summary = models.CharField(_('Summary'), max_length=128)
    description = models.TextField(_('Description about the image'), blank=True,  default='')
    user = models.ForeignKey(User, related_name = 'user_images', verbose_name = 'User')

    catalog = models.ForeignKey(ImageCatalog, related_name = 'catalog_images', verbose_name = _('Image Catalog'))
    origin = models.ForeignKey(ImageOriginInfo, related_name = 'origin_images', verbose_name = _('Image OriginInfo'))

    status = models.IntegerField(_('Image Status'), default = 0, choices = IMAGE_STATUS)
    version = models.IntegerField(_('Image Version'), default = 0)

    filetype = models.IntegerField(_('Image filetype'), default = 3, choices = IMAGE_TYPE)
    filename = models.CharField(_('Image filename'), max_length = 1024)
    resource_protocol = models.IntegerField(_('Resource Protocol'), default = 1, choices = RESOURCE_PROTOCOL)

    logo_filename = models.CharField(_('Logo filename'), max_length = 1024, default = "logo.png")

    size = models.IntegerField(_('File Size'), blank = True, default = 0)
    checksum_type = models.IntegerField(_('Checksum type'), default = 1, choices = CHECKSUM_TYPE)
    checksum_value = models.CharField(_('Checksum value'), max_length = 128, unique = True)

    popularity = models.IntegerField(_('Popularity'), default = 0)

    created = models.DateTimeField(_('Created Time'), auto_now_add = True)
    updated = models.DateTimeField(_('Updated Time'), auto_now = True)

    class Meta:
        ordering = ['-updated']
        db_table = 'image'
        verbose_name = 'Image'
        verbose_name_plural = 'Image'

    def __unicode__(self):
        return self.name

    @property
    def top_path(self):
        return os.path.join(lyc.LY_IMAGE_PATH, str(self.id))

    @property
    def path(self):
        return os.path.join(lyc.LY_IMAGE_PATH, str(self.id), self.checksum_value + '.image')

    @property
    def url_path(self):
        #return os.path.join(lyc.IMAGE_ROOT_URL, self.path)
        return "/images/%s/%s.image" % (self.id, self.checksum_value)

    @property
    def logo_path(self):
        return "%s/%s/logo.png" % (lyc.LY_IMAGE_PATH, self.id)

    @property
    def logo_uri(self):
        real_path = "%s/%s/logo.png" % (lyc.LY_IMAGE_PATH, self.id)
        if os.path.exists(real_path):
            return "/images/%s/%s" % (self.id, self.logo_filename)
        else:
            return "/media/img/default_image_logo.png"

    def checksum(self, path):
        '''
        return a md5sum of the file which specified by path
        '''
        real_path = os.path.join(lyc.LY_IMAGE_UPLOAD_PATH, path)

        fp = open(real_path)
        checksum = hashlib.md5()
        # Fix Me: Maybe can show progress in the future
        while True:
            buffer = fp.read(8192)
            if not buffer: break
            checksum.update(buffer)
        fp.close()
        
        self.checksum_type = 1
        self.checksum_value = checksum.hexdigest()
        # Fix Me: should show the failed case
        return self.checksum_value


    def delete(self, *args, **kwargs):

        if os.path.exists(self.path):
            os.unlink(self.path)

        if os.path.exists(self.logo_path):
            os.unlink(self.logo_path)

        super(Image, self).delete(*args, **kwargs)
