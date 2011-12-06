from lyweb.app.job.models import Job

from lyweb.LuoYunConf import LYWEB_JOB_STATUS


def new_job(user, target_type, target_id, action):

    new_job_status = LYWEB_JOB_STATUS.get('prepare', 0)

    #started = datetime.datetime.now()

    job = Job(user = user, status = new_job_status,
              target_type = target_type,
              target_id = target_id,
              action = action)

    job.save()
    return job
