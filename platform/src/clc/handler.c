#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h> /* gethostname */
#include <netdb.h> /* struct hostent */
#include <sys/epoll.h>

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



int hl_node_register(LyDBConn *db, ComputeNodeQueue *qp,
                     LyRequest *request,
                     int efd, int S /* keep alive socket */)
{
     int ret;

     ret = make_socket_non_blocking(S);
     if (ret == -1)
          return -1;

     // TODO: need authorize

     if ( request->length != sizeof(ComputeNodeInfo) )
     {
          logerror(_("The length of request data(%d) and ComputeNodeInfo(%d) doest not match.\n"), request->length, sizeof(ComputeNodeInfo));
          return -1;
     }

     ComputeNodeItem *nitem;
     nitem = calloc(1, sizeof(ComputeNodeItem));
     if ( nitem == NULL )
     {
          logerror(_("malloc error for ComputeNodeItem.\n"));
          return -1;
     }

     nitem->sfd = S;
     if(ly_recv(S, &(nitem->node), sizeof(ComputeNodeInfo), 0, RECV_TIMEOUT))
     {
          logerror(_("Recv register request data failed.\n"));
          return -1;
     } else
          logdebug(_("Recv register request data success.\n"));

     LyRespond respond;
     respond.length = 0;

     ret = node_register(db, qp, nitem);
     if (ret)
     {
          respond.status = RESPOND_STATUS_FAILED;
     } else {
          respond.status = RESPOND_STATUS_OK;
     }

     // TODO: send should have a retry mechanism
     ret = send(S, &respond, sizeof(LyRespond), 0);
     if (ret == -1)
     {
          logerror(_("Send respond to compute node error.\n"));
          return -1;
     }

     loginfo(_("register compute node success.\n"));

     struct epoll_event ev;
     ev.data.fd = S;
     ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP;
     ret = epoll_ctl (efd, EPOLL_CTL_ADD, S, &ev);
     if (ret == -1)
     {
          logerror(_("Add keep alive socket to epoll error.\n"));
          return -1;
     }

     return 0;
}


int hl_instance_register(LyDBConn *db, LyInstanceQueue *qp,
                         LyRequest *request,
                         int efd, int S /* connect socket */)
{
     int ret;

     ret = make_socket_non_blocking(S);
     if (ret == -1)
          return -1;

     // TODO: need authorize

     if ( request->length != sizeof(DomainInfo) )
     {
          logerror(_("The length of request data(%d) and DomainInfo(%d) doest not match.\n"), request->length, sizeof(DomainInfo));
          return -1;
     }

     LyInstance *ins;
     ins = calloc(1, sizeof(LyInstance));
     if ( ins == NULL )
     {
          logerror(_("Allocate memory for LyInstance failed.\n"));
          return -1;
     }

     ins->sfd = S;

     if(ly_recv(S, &(ins->di), sizeof(DomainInfo), 0, RECV_TIMEOUT))
     {
          logerror(_("Recv instance register request data failed.\n"));
          return -1;
     } else
          logdebug(_("Recv instance register request data success.\n"));

     LyRespond respond;
     respond.length = 0;

     ret = instance_register(db, qp, ins);

     if (ret)
     {
          respond.status = RESPOND_STATUS_FAILED;
          logdebug(_("Register instance %s failed.\n"), ins->di.ip);
     } else {
          respond.status = RESPOND_STATUS_OK;
          logdebug(_("Register instance %s success.\n"), ins->di.ip);
     }

     // TODO: send should have a retry mechanism
     ret = send(S, &respond, sizeof(LyRespond), 0);
     if (ret == -1)
     {
          logerror(_("Send respond to compute node error.\n"));
          return -1;
     }


     struct epoll_event ev;
     ev.data.fd = S;
     ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP;
     ret = epoll_ctl (efd, EPOLL_CTL_ADD, S, &ev);
     if (ret == -1)
     {
          logerror(_("Add keep alive socket to epoll error.\n"));
          return -1;
     }

     return 0;
}

int hl_instance_delete(LyDBConn *db, int S)
{
     // update domain
     DomainInfo di;
     // Fix me, should make sure first.
     di.status = DOMAIN_S_STOP;

     return db_update_instance(db, &di);
}


int hl_new_job(LyDBConn *db, JobQueue *qp,
               int S, /* socket */
               int datalen /* request data length */)
{
     logdebug(_("Start %s.\n"), __func__);

     if (datalen <= 0)
     {
          logerror(_("%s: request data length is %d.\n"), __func__, datalen);
          return -1;
     }

     int32_t job_id;
     if(ly_recv(S, &job_id, 4, 0, RECV_TIMEOUT))
     {
          logerror(_("Get job id failed.\n"));
          return -1;
     }

     pthread_rwlock_wrlock(&qp->q_lock);
     Job *jp = db_get_job(db, qp, job_id);
     pthread_rwlock_unlock(&qp->q_lock);


     if ( jp == NULL )
          return -1;
     else
          logdebug("New job %d: status = %d\n",
                   jp->j_id, jp->j_status);

     // Run the job
     //if (jp->status == JOB_S_PREPARE)
     //     job_run(db, nqp, jqp, jp);

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

     ComputeNodeItem *nitem;
     nitem = calloc(1, sizeof(ComputeNodeItem));
     if ( nitem == NULL )
     {
         logprintfl(LYERROR, "%s: malloc error\n", __func__);
         return -4;
     }

     int recvlen;
     recvlen = recv(RH->sk, &(nitem->node),
                    sizeof(ComputeNodeInfo), 0);
     if ( recvlen != sizeof(ComputeNodeInfo) )
     {
          logprintfl(LYERROR, "update node: read data err,"
                     " read len = %d, data len = %d\n",
                     recvlen, sizeof(ComputeNodeInfo));
          return -3;
     }


     int err = 0;
     //TODO:
     //err = node_update_or_register(qp, nitem);

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
