from tornado.web import url
import app.job.views as job

handlers = [

    # Job
    url(r'/job/([0-9]+)/status', job.JobStatus, name='job:status'),

]
