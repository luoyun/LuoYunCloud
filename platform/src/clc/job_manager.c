#include <sys/socket.h>

#include "control/job_manager.h"
#include "control/node_manager.h"
#include "control/postgres.h"


static int __get_domain_action(int job_action)
{
     switch (job_action) {

     case JOB_ACTION_RUN:
          return LA_DOMAIN_RUN;

     case JOB_ACTION_STOP:
          return LA_DOMAIN_STOP;

     case JOB_ACTION_SUSPEND:
          return LA_DOMAIN_SUSPEND;

     case JOB_ACTION_SAVE:
          return LA_DOMAIN_SAVE;

     case JOB_ACTION_REBOOT:
          return LA_DOMAIN_REBOOT;

     default:
          logerror(_("%s: unknown job action!"), __func__);
          return -1;
     }
}


static int __get_domain_status(int domain_action)
{
     switch (domain_action) {

     case LA_DOMAIN_RUN:
          return DOMAIN_S_RUNNING;

     case LA_DOMAIN_STOP:
          return DOMAIN_S_STOP;

     case LA_DOMAIN_SUSPEND:
          return DOMAIN_S_SUSPEND;

     case LA_DOMAIN_SAVE:
     case LA_DOMAIN_REBOOT:
     default:
          return DOMAIN_S_UNKNOWN;
     }
}


static void
__job_remove (JobQueue *qp, Job *jp)
{
     if (jp == qp->q_head) {
          qp->q_head = jp->j_next;
          if (qp->q_tail == jp)
               qp->q_tail = NULL;
     } else if (jp == qp->q_tail) {
          qp->q_tail = jp->j_prev;
          if (qp->q_head == jp)
               qp->q_head = NULL;
     } else {
          jp->j_prev->j_next = jp->j_next;
          jp->j_next->j_prev = jp->j_prev;
     }
     if (qp->q_count)
          qp->q_count--;
}


static void
__job_is_running (LyDBConn *db, JobQueue *qp, Job *jp)
{
     //pthread_rwlock_wrlock(&qp->q_lock);

     time(&jp->j_started);
     jp->j_status = JOB_S_RUNNING;
     db_update_job_status(db, jp);

     //pthread_rwlock_unlock(&qp->q_lock);
}


static void
__job_is_timeout (LyDBConn *db, JobQueue *qp, Job *jp)
{
     logdebug(_("Job %d is timeout.\n"), jp->j_id);

     //pthread_rwlock_wrlock(&qp->q_lock);

     jp->j_status = JOB_S_TIMEOUT;
     time(&jp->j_ended);

     if (!db_update_job_status(db, jp))
          __job_remove(qp, jp);

     //pthread_rwlock_unlock(&qp->q_lock);
}


static void
__job_is_failed (LyDBConn *db, JobQueue *qp, Job *jp)
{
     logdebug(_("Job %d is failed.\n"), jp->j_id);

     //pthread_rwlock_wrlock(&qp->q_lock);
     
     time(&jp->j_ended);
     jp->j_status = JOB_S_FAILED;

     // If success update job status, remove it.
     if (!db_update_job_status(db, jp))
          __job_remove(qp, jp);

     //pthread_rwlock_unlock(&qp->q_lock);
}


static void
__job_is_unknown (LyDBConn *db, JobQueue *qp, Job *jp)
{
     logdebug(_("Job %d is unknown.\n"), jp->j_id);

     //pthread_rwlock_wrlock(&qp->q_lock);
     
     time(&jp->j_ended);
     jp->j_status = JOB_S_UNKNOWN;

     // If success update job status, remove it.
     if (!db_update_job_status(db, jp))
          __job_remove(qp, jp);

     //pthread_rwlock_unlock(&qp->q_lock);
}


// TODO: finished ?
static void
__job_is_finished (LyDBConn *db, JobQueue *qp, Job *jp)
{
     logdebug(_("Job %d is finished.\n"), jp->j_id);
     //pthread_rwlock_wrlock(&qp->q_lock);
     
     time(&jp->j_ended);
     //jp->j_status = JOB_S_FINISHED;

     // If success update job status, remove it.
     if (!db_update_job_status(db, jp))
          __job_remove(qp, jp);

     //pthread_rwlock_unlock(&qp->q_lock);
}


/* APUE2 11.6 : Initialize a queue */
int job_queue_init(JobQueue *qp)
{
     int err;
     qp->q_head = NULL;
     qp->q_tail = NULL;
     err = pthread_rwlock_init(&qp->q_lock, NULL);
     if (err != 0)
          return err;

     qp->q_count = 0;
     qp->q_gflag = 1;
     qp->q_pflag = 0;
     return 0;
}


/* APUE2 11.6 : Insert a job at the head of the queue. */
void job_insert(JobQueue *qp, Job *jp)
{
     pthread_rwlock_wrlock(&qp->q_lock);

     Job *ljp;
     int job_exist = 0;

     for (ljp = qp->q_head; ljp != NULL; ljp = ljp->j_next)
     {
          if (ljp->j_id == jp->j_id)
          {
               job_exist = 1;
               break;
          }
     }

     if (!job_exist)
     {
          jp->j_next = qp->q_head;
          jp->j_prev = NULL;
          if (qp->q_head != NULL)
               qp->q_head->j_prev = jp;
          else
               qp->q_tail = jp; /* list was empty */
          qp->q_head = jp;
          qp->q_count++;
     }

     pthread_rwlock_unlock(&qp->q_lock);
}

/* APUE2 11.6 : Append a job on the tail of the queue. */
void job_append(JobQueue *qp, Job *jp)
{
     pthread_rwlock_wrlock(&qp->q_lock);

     Job *ljp;
     int job_exist = 0;

     for (ljp = qp->q_head; ljp != NULL; ljp = ljp->j_next)
     {
          if (ljp->j_id == jp->j_id)
          {
               job_exist = 1;
               break;
          }
     }

     if (!job_exist)
     {
          jp->j_next = NULL;
          jp->j_prev = qp->q_tail;
          if (qp->q_tail != NULL)
               qp->q_tail->j_next = jp;
          else
               qp->q_head = jp;
          qp->q_tail = jp;
          qp->q_count++;
     }

     pthread_rwlock_unlock(&qp->q_lock);
}

/* APUE2 11.6 : Remove the given job from a queue. */
void job_remove(JobQueue *qp, Job *jp)
{
     pthread_rwlock_wrlock(&qp->q_lock);
     if (jp == qp->q_head) {
          qp->q_head = jp->j_next;
          if (qp->q_tail == jp)
               qp->q_tail = NULL;
     } else if (jp == qp->q_tail) {
          qp->q_tail = jp->j_prev;
          if (qp->q_head == jp)
               qp->q_head = NULL;
     } else {
          jp->j_prev->j_next = jp->j_next;
          jp->j_next->j_prev = jp->j_prev;
     }
     if (qp->q_count)
          qp->q_count--;
     pthread_rwlock_unlock(&qp->q_lock);
}

/* APUE2 11.6 : Find a job for the given thread ID. */
Job *job_find(JobQueue *qp, pthread_t tid)
{
     Job *jp;

     if (pthread_rwlock_rdlock(&qp->q_lock) != 0)
          return NULL;

     for (jp = qp->q_head; jp != NULL; jp = jp->j_next)
          if (pthread_equal(jp->j_tid, tid))
              break;

     pthread_rwlock_unlock(&qp->q_lock);
     return jp;
}


/* Create a job and return it */
Job *create_job(int sk, LySockHead *sh)
{
     Job *jp = malloc(sizeof(Job));
     if (jp == NULL)
     {
          logprintfl(LYERROR, "create_job: malloc error.\n");
          return NULL;
     }

     jp->j_started = time(&jp->j_started);
     //jp->j_sockhead = sh;
     //jp->j_socket = sk;

     return jp;
}


void print_job_queue(JobQueue *qp)
{
     Job *jp;

     if (qp == NULL)
     {
          logprintfl(LYDEBUG, "queue is empty.\n");
          return;
     }

     if (pthread_rwlock_rdlock(&qp->q_lock) != 0)
     {
          logprintfl(LYERROR, "can not lock queue.\n");
          return;
     }

     logsimple("Current Job Queue:\n");
     for (jp = qp->q_head; jp != NULL; jp = jp->j_next)
     {
          logsimple("  - Job %d : status = %d, started = %ld\n", jp->j_id, jp->j_status, jp->j_started);
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return;
}


/* DB -> JobQueue */
int
get_job_queue (LyDBConn *db, JobQueue *qp)
{
     logdebug("START %s\n", __func__);

     int err;

     pthread_rwlock_wrlock(&qp->q_lock);
     qp->q_gflag = 0;
     err = db_get_jobs2(db, qp);
     if (err)
     {
          logerror("%s: get job queue error\n", __func__);
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return err;
}


/* JobQueue -> DB */
int
put_job_queue (LyDBConn *db, JobQueue *qp)
{
     //logsimple("START %s:%d:%s\n",
     //          __FILE__, __LINE__, __func__);

     time_t now;
     Job *jp;

     pthread_rwlock_wrlock(&qp->q_lock);
     qp->q_pflag = 0;
     now = time(&now);
     // update status of all jobs to DB
     for ( jp = qp->q_head; jp != NULL; jp = jp->j_next )
     {

     }

     pthread_rwlock_unlock(&qp->q_lock);

     return 0;
}



/* job_dispatch: Do with job queue at once
 */
int job_dispatch ( LyDBConn *db,
                   ComputeNodeQueue *nqp,
                   JobQueue *jqp )
{
     logdebug(_("Start %s.\n"), __func__);

     // TODO: blank queue
     if (jqp->q_head == NULL)
          return 0;

     int timeout;
     time_t now;
     Job *jp;

     // TODO: need more effective lock scheme
     //if (pthread_rwlock_rdlock(&jqp->q_lock) != 0)
     //     return -1;
     pthread_rwlock_wrlock(&jqp->q_lock);

     now = time(&now);
     for ( jp = jqp->q_head; jp != NULL; jp = jp->j_next )
     {
          switch (jp->j_status) {

          case JOB_S_PREPARE:
               //TODO: run job thread
               job_run(db, nqp, jqp, jp);
               break;

          case JOB_S_RUNNING:
               //time(&now);
               if (jp->j_target_type == JOB_TARGET_DOMAIN)
                    timeout = DOMAIN_JOB_TIMEOUT;
               else if (jp->j_target_type == JOB_TARGET_NODE)
                    timeout = NODE_JOB_TIMEOUT;
               else
                    timeout = DEFAULT_JOB_TIMEOUT;

               if ((now - jp->j_started) > timeout)
                    __job_is_timeout(db, jqp, jp);
               break;

          case JOB_S_FINISHED:
          case JOB_S_FAILED:
          case JOB_S_CANCLED:
          case JOB_S_PENDING:
          case JOB_S_TIMEOUT:
               __job_is_finished(db, jqp, jp);
               break;

          case JOB_S_QUERYING:
               // TODO: should to querying
               break;

          default:
               __job_is_unknown(db, jqp, jp);
          }
     }

     pthread_rwlock_unlock(&jqp->q_lock);

     return 0;
}


int
job_run ( LyDBConn *db,
          ComputeNodeQueue *nqp,
          JobQueue *jqp,
          Job *jp )
{
     switch (jp->j_target_type) {
     case JOB_TARGET_NODE:
          logdebug("action for node have not complete.");
          break;
     case JOB_TARGET_DOMAIN:
          domain_job_run(db, nqp, jqp, jp);
          //logdebug("Run domain job, but have not completed yet.\n");
          break;

     default:
          break;
     }

     return 0;
}


int domain_job_run ( LyDBConn *db,
                     ComputeNodeQueue *nqp,
                     JobQueue *jqp, Job *jp )
{
     // Does nodes ready ?
     if (nqp->q_head == NULL)
     {
          logdebug(_("Have and node could run job %d yet.\n"), jp->j_id);
          return -1;
     }

     logdebug(_("Starting run job %d\n"), jp->j_id);
     int ret = -1;

     __job_is_running(db, jqp, jp);

     /* 2. get domain info from DB */
     DomainInfo *dip;
     dip = db_get_domain(db, jp->j_target_id);
     if ( dip == NULL )
     {
          __job_is_failed(db, jqp, jp);
          return -1;
     }

     ComputeNodeItem *nitem;
     int new_domain = 1;
     if ( dip->node_id > 0 )
     {
          // does the node of domain is running ?
          if (pthread_rwlock_rdlock(&nqp->q_lock) != 0)
          {
               logerror(_("Can not lock node queue.\n"));
               goto clean;
          }

          for (nitem = nqp->q_head;
               nitem != NULL;
               nitem = nitem->n_next)
               if (nitem->id == dip->node_id &&
                    nitem->node.status == NODE_S_RUNNING)
               {
                    new_domain = 0;
                    break;
               }

          pthread_rwlock_unlock(&nqp->q_lock);
     }

     if (new_domain)
     {
          // new domain, find a node
          nitem = find_node(nqp);
          if (nitem == NULL)
          {
               logerror(_("Can't find a node to run domain %d.\n"), dip->id);
               // TODO: should wait resource! not failed!
               __job_is_failed(db, jqp, jp);
               goto clean;
          }
     }

     // now, nitem is the node.
     dip->node_id = nitem->id;

     // connect to compute node
     int sfd;
     sfd = connect_to_host(nitem->node.ip, nitem->node.port);
     if ( sfd <= 0 )
     {
          logdebug(_("Connect to %s:%d failed.\n"),
                   nitem->node.ip, nitem->node.port);
          __job_is_failed(db, jqp, jp);
          goto clean;
     }

     // TODO: request connect should run in a thread, and
     // update job status dynamically.
     LyRequest request;
     request.type = RQTYPE_DOMAIN_CONTROL;
     request.from = RQTARGET_CONTROL;
     request.length = sizeof(DomainControlData);

     // send request
     if(ly_send(sfd, &request, sizeof(LyRequest), 0, SEND_TIMEOUT))
     {
          logerror(_("Send domain control request header failed.\n"));
          close(sfd);
          __job_is_failed(db, jqp, jp);
          goto clean;
     }


     DomainControlData dcd;
     dcd.id = jp->j_target_id;
     // Make sure the action of Domain Control
     dcd.action = __get_domain_action(jp->j_action);
     if (dcd.action < 0)
     {
          __job_is_failed(db, jqp, jp);
          goto clean;
     }

     if (ly_send(sfd, &dcd, sizeof(DomainControlData), 0, SEND_TIMEOUT))
     {
          logerror(_("Send domain control request data failed: (%d) != (%d)\n"), ret, sizeof(DomainControlData));
          close(sfd);
          __job_is_failed(db, jqp, jp);
          goto clean;
     }


     // Get respond
     // TODO: this maybe a loop, for dynamic job status show.
     LyRespond respond;
     while(1)
     {
          if(ly_recv(sfd, &respond, sizeof(LyRespond), 0, RECV_TIMEOUT))
          {
               logerror(_("Get domain control respond error.\n"));
               close(sfd);
               __job_is_failed(db, jqp, jp);
               goto clean;
          }

          break;
          // TODO: stop just specify status
     }

     // close connect
     close(sfd);


     // if run job failed, then finished the job
     if (respond.status != 0)
     {
          logdebug("start job %d on node %s:%d is failed, "
                   "respond status is %d\n",
                   jp->j_id, nitem->node.ip,
                   nitem->node.port, respond.status);
          __job_is_failed(db, jqp, jp);
     } else {
          logdebug("start job %d on node %s:%d is success\n",
                   jp->j_id, nitem->node.ip,
                   nitem->node.port);
          __job_is_finished(db, jqp, jp);
          dip->status = __get_domain_status(dcd.action);
          ret = db_update_domain_status(db, dip);
     }


clean:
     free(dip);
     return ret;
}
