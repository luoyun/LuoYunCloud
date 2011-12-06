from django.db import models
from django.contrib.auth.models import User

JOB_STATUS = (
    (0, 'UNKNOWN'),
    (1, 'PREPARE'),
    (2, 'RUNNING'),
    (3, 'FINISHED'),
    (4, 'FAILED'),
    (5, 'STOPED'),
    (10, 'PENDING'),
    (11, 'TIMEOUT'),
)

JOB_ACTION = (
    (0, 'UNKNOWN'),
    (1, 'RUN'),
    (2, 'STOP'),
    (3, 'SUSPEND'),
    (4, 'SAVE'),
    (5, 'REBOOT'),
)

JOB_TARGET_TYPE = (
    (0, 'UNKNOWN'),
    (1, 'NODE'),
    (2, 'DOMAIN'),
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

