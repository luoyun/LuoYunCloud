import os, hashlib
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from lyweb import LuoYunConf as lyc

IMAGE_TYPE = ( 
    (0, 'UNKNOWN'),
    (1, 'Kernel'),
    (2, 'Ramdisk'),
    (3, 'Disk'),
    (4, 'ISO'),
)

CHECKSUM_TYPE = (
    (1, 'MD5'),
    (2, 'SHA1'),
)


class Image(models.Model):

    name = models.CharField('Image Name', max_length = 30, blank = True)
    user = models.ForeignKey(User, related_name = 'images', verbose_name = 'User')
    created = models.DateTimeField('Created', auto_now_add = True)
    updated = models.DateTimeField('Updated', auto_now = True)

    type = models.IntegerField('Image type', default = 3,
                               choices = IMAGE_TYPE)
    checksum_value = models.CharField('Checksum value', max_length = 128, unique = True)
    checksum_type = models.IntegerField('Checksum type', default = 1, choices = CHECKSUM_TYPE)
    size = models.IntegerField('File Size', blank = True, default = 0)

    class Meta:
        ordering = ['-updated']
        db_table = 'image'
        verbose_name = 'Image'
        verbose_name_plural = 'Image'

    def __unicode__(self):
        return self.name

    @property
    def path(self):
        return '%s_%s_%s' % (self.type, self.id,
                             self.checksum_value)

    @property
    def url_path(self):
        return os.path.join(lyc.IMAGE_ROOT_URL, self.path)

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
