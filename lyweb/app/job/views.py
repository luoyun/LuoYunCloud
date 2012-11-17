import time
import tornado

from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc

from app.job.models import Job


class JobStatus(LyRequestHandler):

    ''' A running job status '''

    @asynchronous
    def get(self, id):

        job = self.db2.query(Job).get(id)
        if not job:
            return self.write(u'No job %s !' % id)

        try:
            previous = self.get_argument_int('previous', 0)
        except:
            previous = 0

        self.check_job_status(id, previous)


    def check_job_status(self, id, previous):

        if self.request.connection.stream.closed():
            return

        job = self.db2.query(Job).get(id)
        self.db2.commit() # TODO: must commit ?
        #print 'id = %s, previous = %s, now = %s' % (
        #    id, previous, job.status )

        if job.status >= 300 and job.status <= 399:
            json = { 'jid': id, 'job_status': job.status,
                     'desc': job.status_string,
                     'status': 0 }
            self.write(json)
            return self.finish()

        if job.status == previous:

            tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + 3,
                lambda: self.check_job_status(id, job.status) )

        else:

            json = { 'jid': id, 'job_status': job.status,
                     'desc': job.status_string,
                     'status': 1 }
            self.write(json)
            self.finish()
