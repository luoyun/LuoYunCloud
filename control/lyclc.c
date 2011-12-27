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
#include <sys/epoll.h>
#include <pthread.h>



#include "util/luoyun.h"
#include "util/misc.h"
#include "util/lyerrno.h"
#include "control/postgres.h"
#include "control/job_manager.h"
#include "control/handler.h"
#include "control/options.h"
#include "control/instance_manager.h"



#define MAXEPOLLSIZE 10000
#define MAXBUF 1024
#define MAXEVENTS 64

/* global variables */
CtConfig GC;
LyDBConn G_DB;

LyInstanceQueue G_INSQ;
JobQueue G_JOBQ;
ComputeNodeQueue G_NODEQ;


#include <locale.h>
#include <libintl.h>
#define _(S) gettext(S)
#define LOCALEDIR "/usr/share/locale"

void usage(void)
{

     printf (_("\
%s is the controller of LuoYun Cloud Platform.\n\n\
"), PROGRAM_NAME);

     printf (_("\
Usage : %s [OPTION]\n\n\
"), PROGRAM_NAME);

     printf (_(
"  -c, --config        Specify the config file\n"
"                      default is /etc/yu.conf\n"
"  -D, --daemon        run as a daemon\n"
"                      log file specified by -l\n"
"  -l, --log           replace /var/log/lyclc.log\n"

"  -d, --debug         debug mode\n"
"  -v, --verbose       verbose mode\n"));

}


/* Parse the config file of clc server */
int __parse_config(CtConfig *c)
{
     FILE *fp;

     fp = fopen(c->config, "r");
     if ( fp == NULL )
     {
          logerror(_("Can not open config file: %s\n"),
                   c->config);
          return -2;
     }

     loginfo(_("Reading config from %s\n"), c->config);
     char line[LINE_MAX];
     char *kstr; /* point to the key string */
     char *vstr; /* point to the value string */

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
               strcpy(c->host_ip, vstr);

          else if ( (kstr = strstr(line, "HOST_PORT")) != NULL )
               c->host_port = atoi(vstr);

          else if ( (kstr = strstr(line, "DB_NAME")) != NULL )
               strcpy(c->db_name, vstr);

          else if ( (kstr = strstr(line, "DB_USERNAME")) != NULL )
               strcpy(c->db_username, vstr);

          else if ( (kstr = strstr(line, "DB_PASSWORD")) != NULL )
               strcpy(c->db_password, vstr);

          else
               logerror(_("Not support grammar: %s\n"), line);

     }

     return 0;
}


int
__print_config(CtConfig *c)
{
     logdebug(
          "[ CtConfig ]\n"
          "  host_ip = %s\n"
          "  host_port = %d\n"
          "  db_username = %s\n"
          "  db_password = %s\n"
          "  config = %s\n"
          "  log = %s\n"
          "  verbose = %d\n"
          "  debug = %d\n"
          "  daemon = %d\n",
          c->host_ip, c->host_port,
          c->db_username, c->db_password,
          c->config, c->log,
          c->verbose, c->debug, c->daemon );

     return 0;
}


static int __delete_client(int S /* socket fd */)
{
     int ret = 0;

     // client is a node ?
     int id;
     id = get_node_id_by_sfd(&G_NODEQ, S);
     if (id > 0)
     {
          logdebug(_("Client is node(%d).\n"), id);
          ret = node_remove2(&G_DB, &G_NODEQ, S);
          goto clean;
     }

     // client is a instance ?
     id = get_instance_id_by_sfd(&G_INSQ, S);
     if (id > 0)
     {
          logdebug(_("Client is instance(%d).\n"), id);
          ret = instance_remove(&G_DB, &G_INSQ, S);
          goto clean;
     }

     logerror(_("Unknown client.\n"));


     // DEBUG
     print_node_queue(&G_NODEQ);
     print_job_queue(&G_JOBQ);
     print_instance_queue(&G_INSQ);

clean:
     if (!ret)
          logdebug(_("Delete client %d success.\n"), S);
     else
          logdebug(_("Delete client %d failed.\n"), S);

     close(S);

     return ret;
}


static int __new_client(int sfd, int efd)
{
     int ret, infd;
     LyRequest request;

     struct sockaddr in_addr;
     socklen_t in_len;

     char hbuf[NI_MAXHOST], sbuf[NI_MAXSERV];

     in_len = sizeof in_addr;
     infd = accept(sfd, &in_addr, &in_len);
     if (infd == -1)
     {
          if ( (errno != EAGAIN) &&
                  (errno != EWOULDBLOCK) )
               logerror(_("%s: accept failed.\n"), __func__);

          return -1;
     }

     ret = getnameinfo(&in_addr, in_len,
                       hbuf, sizeof hbuf,
                       sbuf, sizeof sbuf,
                       NI_NUMERICHOST | NI_NUMERICSERV);
     if (!ret)
          logdebug("Accepted connection on descriptor %d from %s:%s\n", infd, hbuf, sbuf);

     if (ly_recv(infd, &request, sizeof(LyRequest), 0, RECV_TIMEOUT))
     {
          logerror(_("Recv request header failed.\n"));
          goto clean;
     }

     // Dispatch request
     switch (request.type) {

     case RQTYPE_REGISTER:
          loginfo(_("Register compute node %s.\n"), hbuf);
          if (hl_node_register(&G_DB, &G_NODEQ, &request, efd, infd))
               goto clean;

          job_dispatch(&G_DB, &G_NODEQ, &G_JOBQ);
          print_node_queue(&G_NODEQ);
          return 0;

     case RQTYPE_INSTANCE_REGISTER:
          loginfo(_("Register instance %s.\n"), hbuf);
          if (hl_instance_register(&G_DB, &G_INSQ, &request, efd, infd))
               goto clean;
          return 0;

     case RQTYPE_NEW_JOB:
          logdebug(_("Get new job.\n"));
          print_node_queue(&G_NODEQ);
          print_job_queue(&G_JOBQ);
          print_instance_queue(&G_INSQ);
          hl_new_job(&G_DB, &G_JOBQ, infd, request.length);
          print_node_queue(&G_NODEQ);
          print_job_queue(&G_JOBQ);
          print_instance_queue(&G_INSQ);
          job_dispatch(&G_DB, &G_NODEQ, &G_JOBQ);
          break;

     default:
          logerror(_("unknown request type %d\n"), request.type);
          ret = -1;
     }


clean:
     close(infd);
     logdebug(_("close client connection.\n"));
     return ret;
}


void * job_manager (void *arg)
{
     loginfo("START JOB Manager.\n");

     int timeout = 0;
     for(;;)
     {
          if (G_JOBQ.q_gflag)
          {
               get_job_queue(&G_DB, &G_JOBQ);
               job_dispatch(&G_DB, &G_NODEQ, &G_JOBQ);
          }

          if ( !timeout )
          {
               print_job_queue(&G_JOBQ);
               timeout = 60;
          } else {
               sleep(2);
               timeout--;
          }

          //if (G_JOBQ.q_pflag)
          //     put_job_queue(&G_DB, &G_JOBQ);

     }
     //pthread_exit((void *)0);
}


void * node_manager (void *arg)
{
     loginfo("START Node Manager.\n");
     // TODO: should change to real time check !
     int timeout = 0;
     for(;;)
     {
          if (G_NODEQ.q_gflag)
               get_node_queue(&G_DB, &G_NODEQ);

          if ( !timeout )
          {
               //TODO: some health check to node

               print_node_queue(&G_NODEQ);

               // TODO: domain manager should not here!!!
               //db_update_domains(&G_DB, &G_NODEQ);

               timeout = 60;
          } else {
               sleep(2);
               timeout--;
          }

          //if (G_NODEQ.q_pflag)
          //     put_node_queue(&G_DB, &G_NODEQ);

     }
     //pthread_exit((void *)0);
}



int main (int argc, char *argv[])
{
     #define PACKAGE "luoyun"
     setlocale (LC_ALL, "");
     bindtextdomain (PACKAGE, LOCALEDIR);
     textdomain (PACKAGE);

     /* Init GC */
     *(GC.config) = '\0';
     GC.verbose = 0;
     GC.debug = 0;
     GC.daemon = 0;
     GC.port = 1369;
     sprintf(GC.config, DEFAULT_CONFIG_PATH);
     sprintf(GC.log, DEFAULT_LOG_PATH);


     int optind;
     optind = parse_opt(argc, argv, &GC);
     if (optind < 0)
     {
          if (optind == -1)
          {
               usage ();
               return 0;
          }

          printf(_("parse options error\n"));
          return -2;
     }


     // TODO: already_running();
     /* Daemonize the progress */
     if (GC.daemon)
     {
          if (GC.debug)
               lyu_daemonize(GC.log, LYDEBUG);
          else
               lyu_daemonize(GC.log, LYINFO);
     }


     /* Parse configure */
     if ( __parse_config(&GC) )
          return -3;

     __print_config(&GC);


     /* Connect to DB */
     G_DB.conn = db_connect(GC.db_name,
                            GC.db_username,
                            GC.db_password);
     if (G_DB.conn == NULL)
     {
          logerror(_("Connect to db failed!"));
          return -3;
     }

     pthread_mutex_init(&G_DB.lock, NULL);

     /* Init instance queue*/
     instance_queue_init(&G_INSQ);

     /* Init node queue */
     node_queue_init(&G_NODEQ);

     /* Init Job Quque */
     job_queue_init(&G_JOBQ);

     int ret;

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
     char str_port[16];
     sprintf(str_port, "%d", GC.port);
     int listener;
     listener = create_and_bind( str_port );
     if ( listener < 0 )
          return -1;

     ret = make_socket_non_blocking(listener);
     if ( ret < 0 )
          return -1;

     ret = listen(listener, SOMAXCONN);
     if (ret == -1)
     {
          perror ("listen");
          return -1;
     }

     int efd;
     efd = epoll_create(MAXEPOLLSIZE);
     if (efd == -1)
     {
          perror("epoll_create");
          return -1;
     }

     struct epoll_event ev;
     ev.events = EPOLLIN | EPOLLET;
     ev.data.fd = listener;
     ret = epoll_ctl(efd, EPOLL_CTL_ADD, listener, &ev);
     if ( ret < 0)
     {
          logerror("Add listener to epoll error.\n");
          return -1;
     } else {
          loginfo("add listener to epoll success.\n");
     }

     struct epoll_event *events;
     events = calloc(MAXEVENTS, sizeof(ev));


     LyRequest request;
     int wlen = sizeof(LyRequest); /* Wanted length */
     int glen; /* Read len */
     int n, i;

     while(1)
     {
          n = epoll_wait(efd, events, MAXEVENTS, -1);
          for (i = 0; i < n; i++)
          {
               if (events[i].events & EPOLLRDHUP)
               {
                    logdebug(_("client %d close\n"),
                             events[i].data.fd);
                    // for node, change it's status in DB
                    __delete_client(events[i].data.fd);
                    // TODO:
               }

               else if ((events[i].events & EPOLLERR) ||
                   (events[i].events & EPOLLHUP) ||
                   (!(events[i].events & EPOLLIN)))
               {
                    logerror("epoll error\n");
                    close(events[i].data.fd);
               }

               else if (listener == events[i].data.fd)
               {
                    /* New client comming */
                    __new_client(listener, efd);
               }

               else
               {
                    /* Some socket have request */
                    glen = recv(events[i].data.fd, &request, wlen, 0);
                    if ( glen != wlen )
                    {
                         logerror("read request error.\n");
                         close(events[i].data.fd);
                    }

                    switch (request.type)
                    {
                    case RQTYPE_REGISTER:
                         loginfo("type = RQTYPE_REGISTER \n");
                         break;

                    case RQTYPE_KEEP_ALIVE:
                         loginfo("type = RQTYPE_REGISTER \n");
                         break;

                    default:
                         loginfo("unknown type %s\n", request.type);
                    }
               }
          }
     }


     /* Clean system */

     free(events);
     close(listener);

     PQfinish(G_DB.conn);

     // TODO: Join the threads

     return 0;
}
