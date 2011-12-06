#include <sys/socket.h>

#include "control/job_manager.h"
#include "control/node_manager.h"
#include "control/postgres.h"


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
     logdebug("%s:%d:%s job %d is timeout\n",
              __FILE__, __LINE__, __func__, jp->j_id);

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
     logdebug("%s:%d:%s job %d is failed\n",
              __FILE__, __LINE__, __func__, jp->j_id);

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
     logdebug("%s:%d:%s job %d is unknown\n",
              __FILE__, __LINE__, __func__, jp->j_id);

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


int job_queue_print(JobQueue *qp)
{
     logdebug("START %s:%d:%s\n",
              __FILE__, __LINE__, __func__);

     Job *jp;

     if (qp == NULL)
     {
          logprintfl(LYDEBUG, "queue is empty.\n");
          return 0;
     }

     if (pthread_rwlock_rdlock(&qp->q_lock) != 0)
     {
          logprintfl(LYERROR, "can not lock queue.\n");
          return -1;
     }

     for (jp = qp->q_head; jp != NULL; jp = jp->j_next)
     {
          logsimple("{"
                    "j_id = %d, "
                    "j_status = %d, "
                    "j_created = %ld, "
                    "j_started = %ld"
                    "}\n", 
                    jp->j_id,
                    jp->j_status,
                    jp->j_created,
                    jp->j_started);
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}


/* DB -> JobQueue */
int
get_job_queue (LyDBConn *db, JobQueue *qp)
{
     logdebug("START %s:%d:%s\n",
              __FILE__, __LINE__, __func__);

     int err;

     pthread_rwlock_wrlock(&qp->q_lock);
     qp->q_gflag = 0;
     err = db_get_jobs(db, qp);
     if (err)
     {
          logerror("%s:%d:%s get job queue from DB error\n",
                   __FILE__, __LINE__, __func__);
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


/* if the status is JOB_S_RUNNING and time is out, 
   then change status to JOB_S_TIMEOUT */
int
job_dispatch ( LyDBConn *db,
               ComputeNodeQueue *nqp,
               JobQueue *jqp )
{
     //logsimple("START %s:%d:%s\n",
     //          __FILE__, __LINE__, __func__);

     // TODO: blank queue
     if (jqp->q_head == NULL)
          return 0;

     int timeout = 1200;
     int interval;
     int update_interval = 6;
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
               time(&now);
               interval = now - jp->j_started;

               if (interval > timeout)
                    __job_is_timeout(db, jqp, jp);
               else if (interval > update_interval)
                    __job_is_running(db, jqp, jp);

               break;

          case JOB_S_FINISHED:
          case JOB_S_FAILED:
          case JOB_S_CANCLED:
          case JOB_S_PENDING:
          case JOB_S_TIMEOUT:
               __job_is_finished(db, jqp, jp);
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
          break;

     default:
          break;
     }

     return 0;
}


int
domain_job_run ( LyDBConn *db,
                 ComputeNodeQueue *nqp,
                 JobQueue *jqp, Job *jp )
{
     logdebug("%s:%d:%s run job %d\n",
              __FILE__, __LINE__, __func__, jp->j_id);

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
     if ( dip->node > 0 )
     {
          // does the node of domain is running ?
          if (pthread_rwlock_rdlock(&nqp->q_lock) != 0)
          {
               logerror("can not lock node queue.\n");
               free(dip);
               return -2;
          }

          for (nitem = nqp->q_head;
               nitem != NULL;
               nitem = nitem->n_next)
               if (nitem->n_id == dip->node &&
                    nitem->n_info->status == NODE_S_RUNNING)
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
               // TODO: should wait resource! not failed!
               logerror("can't find node to run domain\n");
               __job_is_failed(db, jqp, jp);
               free(dip);
               return -2;
          }
     }

     // now, nitem is the node.
     dip->node = nitem->n_id;

     // connect to compute node
     int sk, err;
     sk = connect_to_host(nitem->n_info->ip,
                          nitem->n_info->port);
     if ( sk <= 0 )
     {
          logdebug("failed to connect to %s:%d\n",
                   nitem->n_info->ip, nitem->n_info->port);
          free(dip);
          __job_is_failed(db, jqp, jp);
          return -1;
     }

     LySockRequest request;
     request.from = LST_CONTROL_S;
     request.to = LST_COMPUTE_S;
     request.type = 0;
     if (jp->j_action == JOB_ACTION_RUN)
          request.action = LA_DOMAIN_RUN;
     else if (jp->j_action == JOB_ACTION_STOP)
          request.action = LA_DOMAIN_STOP;
     else if (jp->j_action == JOB_ACTION_SUSPEND)
          request.action = LA_DOMAIN_SUSPEND;
     else if (jp->j_action == JOB_ACTION_SAVE)
          request.action = LA_DOMAIN_SAVE;
     else if (jp->j_action == JOB_ACTION_REBOOT)
          request.action = LA_DOMAIN_REBOOT;
     else {
          logerror("%s: unknown job action!", __func__);
          close(sk);
          free(dip);
          __job_is_failed(db, jqp, jp);
          return -1;
     }
     request.datalen = sizeof(DomainInfo);

     // send request
     err = send(sk, &request, sizeof(LySockRequest), 0);
     err += send(sk, dip, sizeof(DomainInfo), 0);
     if ( -1 == err )
     {
          logerror("%s:%d:%s send msg to %s:%d error\n",
                   __FILE__, __LINE__, __func__,
                   nitem->n_info->ip, nitem->n_info->port);
          close(sk);
          free(dip);
          __job_is_failed(db, jqp, jp);
          return -2;
     }

     // recv the respond
     LySockRespond respond;
     int recvlen;
     recvlen = recv(sk, &respond, sizeof(LySockRespond), 0);

     // close connect
     close(sk);

     if (recvlen != sizeof(LySockRespond))
     {
          logerror("%s: read respond err\n", __func__);
          free(dip);
          __job_is_failed(db, jqp, jp);
          return -3;
     }

     // if run job failed, then finished the job
     if (respond.status != 0)
     {
          logdebug("start job %d on node %s:%d is failed, "
                   "respond status is %d\n",
                   jp->j_id, nitem->n_info->ip,
                   nitem->n_info->port, respond.status);
          __job_is_failed(db, jqp, jp);
     } else {
          logdebug("start job %d on node %s:%d is success\n",
                   jp->j_id, nitem->n_info->ip,
                   nitem->n_info->port);
          __job_is_running(db, jqp, jp);
     }

     free(dip);
     return respond.status;
}
