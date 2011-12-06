#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h> /* gethostname */
#include <netdb.h> /* struct hostent */

#include <pthread.h>


#include "util/luoyun.h"
#include "util/misc.h"
#include "util/lyerrno.h"
#include "control/postgres.h"
#include "control/job_manager.h"
#include "control/handler.h"

/*
#define free(p)  do {                          \
        printf("%s:%d:%s:free(0x%lx)\n",       \
               __FILE__, __LINE__,  __func__,  \
               (unsigned long)p);              \
        free(p);                               \
} while (0)
*/
#include <libpq-fe.h>
typedef struct ServerConfig_t {
     char host_ip[MAX_IP_LEN]; /* control server ip */
     int  host_port;

     char db_name[MAX_USERNAME_LEN];
     char db_username[MAX_USERNAME_LEN];
     char db_password[MAX_PASSWORD_LEN];
} ServerConfig;



/* global queue */
LyDBConn G_DB;

JobQueue G_JOBQ;
ComputeNodeQueue G_NODEQ;



/* Parse the config file of clc server to ServerConfig struct. */
int
__parse_config(const char *file,
                     ServerConfig *sc)
{
     FILE *fp;
     char line[LINE_MAX];
     char *kstr; /* point to the key string */
     char *vstr; /* point to the value string */

     fp = fopen(file, "r");
     if ( fp == NULL )
     {
          logprintfl(LYERROR, _("Can not open config file: %s\n"), file);
          return FILE_OPEN_ERROR;
     }

     while ( 1 )
     {
          if ( fgets(line, LINE_MAX, fp) == NULL )
               break;

          if ( str_filter_white_space(line) != 0 ) continue;

          vstr = strstr(line, "=");
          if ( vstr == NULL )
               continue;
          else
               vstr++;

          if ( (kstr = strstr(line, "HOST_IP")) != NULL )
               strcpy(sc->host_ip, vstr);

          else if ( (kstr = strstr(line, "HOST_PORT")) != NULL )
               sc->host_port = atoi(vstr);

          else if ( (kstr = strstr(line, "DB_NAME")) != NULL )
               strcpy(sc->db_name, vstr);

          else if ( (kstr = strstr(line, "DB_USERNAME")) != NULL )
               strcpy(sc->db_username, vstr);

          else if ( (kstr = strstr(line, "DB_PASSWORD")) != NULL )
               strcpy(sc->db_password, vstr);

          else
               logprintfl(LYERROR, _("Not support grammar: %s\n"), line);

     }

     return 0;
}


int
__print_config(ServerConfig *sc)
{
     printf(
          "ServerConfig = {\n"
          "  host_ip = %s\n"
          "  host_port = %d\n"
          "  db_username = %s\n"
          "  db_password = %s\n"
          "}\n",
          sc->host_ip, sc->host_port,
          sc->db_username, sc->db_password);
     return 0;
}



void * job_manager (void *arg)
{
     logdebug("START JOB Manager\n");

     int timeout = 0;
     for(;;)
     {
          if (G_JOBQ.q_gflag)
               get_job_queue(&G_DB, &G_JOBQ);

          job_dispatch(&G_DB, &G_NODEQ, &G_JOBQ);

          if ( !timeout )
          {
               job_queue_print(&G_JOBQ);
               timeout = 10;
          } else {
               sleep(1);
               timeout--;
          }

          //if (G_JOBQ.q_pflag)
          //     put_job_queue(&G_DB, &G_JOBQ);

     }
     //pthread_exit((void *)0);
}


void * node_manager (void *arg)
{
     logdebug("Node Manager started.\n");
     // TODO: should change to real time check !
     int timeout = 0;
     for(;;)
     {
          if (G_NODEQ.q_gflag)
               get_node_queue(&G_DB, &G_NODEQ);

          if ( !timeout )
          {
               //TODO: some health check to node

               /* 1. timeout
                  if status is NODE_S_RUNNING and timeout,
                  then change status to NODE_S_UNKNOWN */
               node_timeout_check(&G_NODEQ, 60);

               print_node_queue(&G_NODEQ);

               // TODO: domain manager should not here!!!
               db_update_domains(&G_DB, &G_NODEQ);

               timeout = 6;
          } else {
               sleep(2);
               timeout--;
          }

          if (G_NODEQ.q_pflag)
               put_node_queue(&G_DB, &G_NODEQ);

     }
     //pthread_exit((void *)0);
}


void *__request_handler (void *arg)
{
     // TODO: make a good detach method
     pthread_detach(pthread_self());

     LySockRequestHandler *rh;
     rh = (LySockRequestHandler *)arg;

     LySockRequest *rq;
     rq = rh->request;

     logdebug("handler { %d => %d, type = %d, "
              "action = %d, datalen = %d }\n",
              rq->from, rq->to,
              rq->type, rq->action,
              rq->datalen);

     switch (rq->action) {

     case LA_WEB_NEW_JOB:
          hl_new_job(&G_DB, rh, &G_JOBQ);
          break;

     case LA_CP_UPDATE_STATUS:
          hl_node_status(rh, &G_NODEQ);
          break;

     case LA_DOMAIN_STATUS:
          hl_domain_status(&G_DB, rh, &G_JOBQ);
          break;

     case LA_CP_GET_IMAGE_INFO:
          hl_get_image_info(&G_DB, rh);
          break;
                    
     default:
          logprintfl(LYERROR, "Unknown request action: %d\n",
                     rh->request->action);
     }


     close(rh->sk);
     free(rh->request);
     free(rh);

     pthread_exit((void *)0);
}



int main (int argc, char *argv[])
{
     int ret;

     if ( argc < 3 )
     {
          printf("Usage: %s node service\n", argv[0]);
          return -1;
     }


     // TODO: already_running();


     /* Parse configure */
     ServerConfig *sc;
     sc = malloc(sizeof(ServerConfig));
     if (sc == NULL)
     {
          logprintfl(LYERROR, "malloc error.\n");
          return -2;
     }
     const char *c_file = "/opt/LuoYunSrc/tools/luoyu.conf";
     __parse_config(c_file, sc);
     __print_config(sc);

     /* Connect to DB */
     G_DB.conn = db_connect(sc->db_name,
                             sc->db_username,
                             sc->db_password);
     if (G_DB.conn == NULL)
     {
          logprintfl(LYERROR, "Connect to db failed!\n");
          return -3;
     }

     pthread_mutex_init(&G_DB.lock, NULL);


     /* Init node queue */
     node_queue_init(&G_NODEQ);



     /* Init Job Quque */
     job_queue_init(&G_JOBQ);


     /* Daemonize the progress */
     //lyu_daemonize("/tmp/control.log");


     /* Node manage thread */
     pthread_t node_manager_tid;
     ret = pthread_create(&node_manager_tid, NULL,
                          node_manager, NULL);
     if (ret != 0)
     {
          if (ret == EAGAIN)
               logerror("System limited, can't create thread\n");
          else if ( ret == EINVAL )
               logerror("Invalid settings in attr\n");
          else if ( ret == EPERM )
               logerror("No permission to set the scheduling policy and parameters specified in attr\n");

          // TODO: release the system resources
          return -2;
     }

     /* TODO: how to make this thread safe ? */
     //sleep(3);

     /* Job manage thread */
     pthread_t job_manager_tid;
     ret = pthread_create( &job_manager_tid, NULL,
                           job_manager, NULL );
     if (ret != 0)
     {
          if (ret == EAGAIN)
               logerror("System limited, can't create thread\n");
          else if ( ret == EINVAL )
               logerror("Invalid settings in attr\n");
          else if ( ret == EPERM )
               logerror("No permission to set the scheduling policy and parameters specified in attr\n");

          // TODO: release the system resources
          return -2;
     }


     // TODO: wait all threads run.

     /* Create a socket and listen on it */
     int sfd;
     sfd = create_socket(argv[1], argv[2]);

     int nsfd; /* new socket connect */
     struct sockaddr nskaddr;
     struct sockaddr_in *nskaddr_in;
     socklen_t size_skaddr = sizeof(struct sockaddr);

     LySockRequest *request;
     LySockRequestHandler *RH;
     pthread_t handler_tid; // TODO: does this have problem ?
     int recvlen;

     for (;;)
     {
          nsfd = accept(sfd, &nskaddr, &size_skaddr);
          if ( nsfd < 0 )
          {
               // TODO:
               logprintfl(LYERROR, "%s: accept error, "
                          "nsfd = %d\n", __func__, nsfd);
               sleep(1);
               continue;
          }
          //logprintfl(LYDEBUG, "nsfd = %d\n", nsfd);

          nskaddr_in = (struct sockaddr_in *)&nskaddr;
          logdebug("FROM: %s:%d\n",
                   inet_ntoa(nskaddr_in->sin_addr),
                   ntohs(nskaddr_in->sin_port));

          request = malloc( sizeof(LySockRequest) );
          if (request == NULL)
          {
               logerror("request malloc error,"
                          "close connect.\n");
               close(nsfd);
               continue;
          }

          recvlen = recv(nsfd, request,
                         sizeof(LySockRequest), 0);
          if ( recvlen != sizeof(LySockRequest) )
          {
               logprintfl(LYERROR, "read request error.\n");
               close(nsfd);
          }

          // TODO: if request number is limited, wait.

          // TODO: if request action is quit from the man server

          RH = malloc( sizeof(LySockRequestHandler) );
          if ( RH == NULL )
          {
               logprintfl(LYERROR, "%s: malloc err, "
                          "close connect.\n", __func__);
               close(nsfd);
               continue;
          }
          RH->request = request;
          RH->sk = nsfd;

          ret = pthread_create(&handler_tid, NULL, 
                               __request_handler, RH);
          if (ret != 0) {
               if (ret == EAGAIN)
                    logerror("System limited, can't create thread\n");
               else if ( ret == EINVAL )
                    logerror("Invalid settings in attr\n");
               else if ( ret == EPERM )
                    logerror("No permission to set the scheduling policy and parameters specified in attr\n");

               continue;
          }

     }

     /* Clean system */
     close(sfd);
     PQfinish(G_DB.conn);

     // TODO: Join the threads

     return 0;
}
