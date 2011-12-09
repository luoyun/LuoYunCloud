from django.utils.translation import ugettext as _

from django.db import models
from django.contrib.auth.models import User

JOB_STATUS = (
    (0, _('UNKNOWN')),
    (1, _('PREPARE')),
    (2, _('RUNNING')),
    (3, _('FINISHED')),
    (4, _('FAILED')),
    (5, _('STOPED')),
    (10, _('PENDING')),
    (11, _('TIMEOUT')),
)

JOB_ACTION = (
    (0, _('UNKNOWN')),
    (1, _('RUN')),
    (2, _('STOP')),
    (3, _('SUSPEND')),
    (4, _('SAVE')),
    (5, _('REBOOT')),
)

JOB_TARGET_TYPE = (
    (0, _('UNKNOWN')),
    (1, _('NODE')),
    (2, _('DOMAIN')),
)

class Job(models.Model):

    user = models.ForeignKey(User, related_name = 'user_jobs', verbose_name = 'User')
    status = models.IntegerField('Job Status', default = 0, choices = JOB_STATUS)

    created = models.DateTimeField('Created Time', auto_now_add = True)
    started = models.DateTimeField('Started Time', blank = True, null = True)
    ended = models.DateTimeField('Ended Time', blank = True, null = True)

    target_type = models.IntegerField('Target Type', default = 0, choices = JOB_TARGET_TYPE)
    target_id = models.IntegerField('Target Id', default = 0)

    action = models.IntegerField('Action', default = 0, choices = JOB_ACTION)

    class Meta:
        ordering = ['-id']
        db_table = 'job'
        verbose_name = 'Job'
        verbose_name_plural = 'Job'

