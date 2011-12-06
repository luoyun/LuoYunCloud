#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h> /* gethostname */
#include <netdb.h> /* struct hostent */

#include "util/misc.h"
#include "util/luoyun.h"
#include "control/postgres.h"


#include "control/handler.h"


static int __send_respond ( int sk, int status,
                            int datalen, void *data );


/* send respond to compute server */
static int
__send_respond ( int sk, int status,
                 int datalen, void *data )
{

     LySockRespond respond;
     respond.status = status;
     respond.from = LST_CONTROL_S;
     respond.to = LST_COMPUTE_S;
     respond.used_time = 0;
     respond.datalen = datalen;

     int err;

     err = send(sk, &respond, sizeof(LySockRespond), 0);
     if (datalen)
          err += send(sk, data, datalen, 0);

     if ( -1 == err )
     {
          logprintfl(LYERROR, "%s: could not send respond "
                     "to compute server\n", __func__);
     } else {
          logprintfl(LYDEBUG, "%s: send respond to compute "
                     "server success, status = %d\n",
                     __func__, status);
     }


     return err;
}


int
hl_new_job ( LyDBConn *db,
             LySockRequestHandler *RH,
             JobQueue *qp )
{
     logdebug("LA_WEB_NEW_JOB %s:%d:%s\n",
              __FILE__, __LINE__, __func__);

     if (RH->request->datalen <= 0)
     {
          logprintfl(LYERROR,
                     "%s:%d:%s => request format err,"
                     "datalen = %d\n",
                     __FILE__, __LINE__, __func__,
                     RH->request->datalen);
          return -1;
     }

     int job_id;
     int recvlen;
     recvlen = recv(RH->sk, &job_id, sizeof(int), 0);
     if ( recvlen != sizeof(int) )
     {
          logerror("get job id error, "
                   "read len = %d, data len = %d\n",
                   recvlen, sizeof(int));
          return -2;
     }

     pthread_rwlock_wrlock(&qp->q_lock);
     Job *jp = db_get_job(db, qp, job_id);
     pthread_rwlock_unlock(&qp->q_lock);

     if ( jp == NULL )
          return -1;
     else
          logdebug("New job %d: status = %d\n",
                   jp->j_id, jp->j_status);

     return 0;
}


/* ComputeNode -> ControlNode: completed job */
int
hl_domain_status ( LyDBConn *db,
                   LySockRequestHandler *RH,
                   JobQueue *qp )
{
     //logdebug("%s:%d:%s\n",
     //          __FILE__, __LINE__, __func__);

     if (RH->request->datalen != sizeof(DomainInfo))
     {
          logerror("%s:%d:%s => request format err,"
                   "datalen = %d\n",
                   __FILE__, __LINE__, __func__,
                   RH->request->datalen);
          return -1;
     }

     DomainInfo di;
     int recvlen;
     recvlen = recv(RH->sk, &di, sizeof(DomainInfo), 0);
     if ( recvlen != sizeof(DomainInfo) )
     {
          logerror("get DomainInfo error, "
                   "read len = %d, data len = %d\n",
                   recvlen, sizeof(DomainInfo));
          return -2;
     }

     logdebug("LA_DOMAIN_STATUS: update domain %d\n", di.id);

     // TODO: in spite of the job status!
     // update job status to finished
     pthread_rwlock_wrlock(&qp->q_lock);
     Job *jp;
     for (jp = qp->q_head; jp != NULL; jp = jp->j_next)
     {
          if (jp->j_target_type != JOB_TARGET_DOMAIN ||
              jp->j_target_id != di.id ||
              jp->j_status == JOB_S_PREPARE)
               continue;

          JobStatus js = JOB_S_FAILED;

          switch (jp->j_action) {
          case JOB_ACTION_REBOOT:
          case JOB_ACTION_RUN:
               if (di.status == DOMAIN_S_RUNNING)
                    js = JOB_S_FINISHED;
               break;
          case JOB_ACTION_STOP:
               if (di.status == DOMAIN_S_STOP)
                    js = JOB_S_FINISHED;
               break;
          case JOB_ACTION_SUSPEND:
               if (di.status == DOMAIN_S_SUSPEND)
                    js = JOB_S_FINISHED;
               break;
          case JOB_ACTION_SAVE:
               js = JOB_S_FINISHED;
               break;
          default:
               js = JOB_S_UNKNOWN;
          }

          logdebug("update domain: change job status\n");
          jp->j_status = js;
          time(&jp->j_ended);
          //db_update_job_status(qp->q_conn, jp);
          // TODO: if jp is completed, delete it from queue !
          //break; //TODO: clean the job queue
     }
     pthread_rwlock_unlock(&qp->q_lock);

     // update domain info
     int err;
     err = db_update_domain_status(db, &di);

     return err;
}


int
hl_node_status ( LySockRequestHandler *RH,
                 ComputeNodeQueue *qp )
{
     //logsimple("START %s:%d:%s\n",
     //          __FILE__, __LINE__, __func__);

     //logdebug("do LA_CP_UPDATE_STATUS\n");

     if (RH->request->datalen <= 0)
     {
          logprintfl(LYERROR,
                     "%s:%d:%s => request format err\n",
                     __FILE__, __LINE__, __func__);
          return -1;
     }

     ComputeNodeInfo *ninfo;
     ninfo = malloc( sizeof(ComputeNodeInfo) );
     if ( ninfo == NULL )
     {
          logprintfl(LYERROR, "updata node: malloc err\n");
          return -2;
     }
     memset(ninfo, 0, sizeof(ComputeNodeInfo));

     int recvlen;
     recvlen = recv(RH->sk, ninfo,
                    sizeof(ComputeNodeInfo), 0);
     if ( recvlen != sizeof(ComputeNodeInfo) )
     {
          logprintfl(LYERROR, "update node: read data err,"
                     " read len = %d, data len = %d\n",
                     recvlen, sizeof(ComputeNodeInfo));
          return -3;
     }

     ComputeNodeItem *nitem;
     nitem = malloc( sizeof(ComputeNodeItem) );
     if ( nitem == NULL )
     {
         logprintfl(LYERROR, "%s: malloc error\n", __func__);
         free(ninfo);
         return -4;
     }
     nitem->n_info = ninfo;
     nitem->n_id = 0;

     int err;
     err = node_update_or_register(qp, nitem);

     LySockRespond respond;
     respond.status = err;
     respond.from = LST_CONTROL_S;
     respond.to = LST_COMPUTE_S;
     respond.used_time = 0;
     respond.datalen = 0;

     err = send(RH->sk, &respond, sizeof(LySockRespond), 0);
     if ( -1 == err )
     {
          logprintfl(LYERROR, "update node: send msg err\n");
          return -5;
     }

     return 0;
}


/* ControlNode -> ComputeNode: give ImageInfo */
int
hl_get_image_info ( LyDBConn *db,
                    LySockRequestHandler *RH )
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

     logprintfl(LYDEBUG, "LA_CP_GET_IMAGE_INFO\n");

     if (RH->request->datalen <= 0)
     {
          logprintfl(LYERROR,
                     "%s:%d:%s => request format err, "
                     "datalen = %d\n",
                     __FILE__, __LINE__, __func__,
                     RH->request->datalen);
          return -1;
     }

     int imgid;
     int recvlen;
     recvlen = recv(RH->sk, &imgid, sizeof(int), 0);
     if ( recvlen != sizeof(int) )
     {
          logprintfl(LYERROR, "update node: read data err,"
                     " read len = %d, data len = %d\n",
                     recvlen, sizeof(int));
          return -2;
     }

     ImageInfo *iip;
     iip = db_get_image(db, imgid);
     if (iip == NULL)
          return -3;

     // send the respond to compute server
     int err;
     err = __send_respond (RH->sk, 0, sizeof(ImageInfo), iip);
     if (err)
          return -4;

     return 0;
}
