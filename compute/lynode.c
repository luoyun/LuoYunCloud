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
#include "domain.h"
#include "node.h"
#include "handler.h"


#include "lynode.h"
#include "options.h"

#define MAX_EVENTS 10

/* Global value */
CpConfig *g_c;


void usage(void)
{

     printf (_("\
%s is the node client of LuoYun Cloud Platform.\n\n\
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


/* Parse the config file of compute server */
int __parse_config( CpConfig *c )
{
     FILE *fp;
     fp = fopen(c->config, "r");
     if ( fp == NULL )
     {
          logerror( _("Can not open config file: %s\n"),
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

          else if ( (kstr = strstr(line, "CONTROL_SERVER_IP")) != NULL )
               strcpy(c->cts_ip, vstr);

          else if ( (kstr = strstr(line, "CONTROL_SERVER_PORT")) != NULL )
               c->cts_port = atoi(vstr);

          else if ( (kstr = strstr(line, "ROOT_PATH")) != NULL )
               strcpy(c->root_path, vstr);

          else
               logerror(_("Not support grammar: %s\n"), line);

     }

     return 0;
}

static int __print_config( CpConfig *c )
{
     logdebug(
          "CpConfig :\n"
          "  host_ip = %s\n"  "  host_port = %d\n"
          "  cts_ip = %s\n"   "  cts_port = %d\n"
          "  root_path = %s\n""  conn = %d\n"
          "  config = %s\n"
          "  log = %s\n"      "  verbose = %d\n"
          "  debug = %d\n"    "  daemon = %d\n",
          c->host_ip, c->host_port,
          c->cts_ip, c->cts_port,
          c->root_path, c->conn,
          c->config,
          c->log, c->verbose,
          c->debug, c->daemon);

     return 0;
}


/* global queue */
LyComputeServerConfig *g_sc = NULL;


int update_compute_node_info (LyComputeServerConfig *sc)
{
     int sk, err;

     sk = connect_to_host(sc->cts_ip, sc->cts_port);
     if ( sk <= 0 ) return -1;

     LySockRequest request;
     request.from = LST_COMPUTE_S;
     request.to = LST_CONTROL_S;
     request.type = 0;
     request.action = LA_CP_UPDATE_STATUS;
     request.datalen = sizeof(ComputeNodeInfo);

     //logsimple("N = { ip = %s, port = %d }\n",
     //          sc->node->ip, sc->node->port);

     err = send(sk, &request, sizeof(LySockRequest), 0);
     err += send(sk, sc->node, sizeof(ComputeNodeInfo), 0);

     if ( -1 == err )
     {
          logprintfl(LYERROR, "%s: update node status err\n", __func__);
          close(sk);
          return -2;
     }

     // TODO: receive respond.

     close(sk);
     return 0;
}


void * __update_status_manager (void *arg)
{
     logprintfl(LYDEBUG, "Update status manager started.\n");
     LyComputeServerConfig *sc;
     sc = (LyComputeServerConfig *)arg;
     int timeout = 0;
     for(;;)
     {
          if ( !timeout )
          {
               logprintfl(LYDEBUG, "COMPUTE NODE: update status\n");
               node_dynamic_status(sc);
               //update_compute_node_info(sc);
               timeout = 6;
          } else {
               sleep(1);
               timeout--;
          }
     }
     //pthread_exit((void *)0);
}


static int __new_client(int sfd, int efd)
{
     LyRequest request;
     int ret;

     memset(&request, 0, sizeof(request));

     struct sockaddr in_addr;
     socklen_t in_len;
     int infd;
     char hbuf[NI_MAXHOST], sbuf[NI_MAXSERV];

     in_len = sizeof in_addr;
     infd = accept(sfd, &in_addr, &in_len);
     if (infd == -1)
     {
          if ((errno == EAGAIN) ||
              (errno == EWOULDBLOCK))
          {
               /* We have processed all incoming
                  connections. */
               goto clean;
          }
          else
          {
               perror ("accept");
               goto clean;
          }
     }

     ret = getnameinfo(&in_addr, in_len,
                       hbuf, sizeof hbuf,
                       sbuf, sizeof sbuf,
                       NI_NUMERICHOST | NI_NUMERICSERV);
     if (ret == 0)
     {
          loginfo("Accepted connection on descriptor %d "
                  "from %s:%s\n", infd, hbuf, sbuf);
     }

     if(ly_recv(infd, &request, sizeof(LyRequest), 0, RECV_TIMEOUT))
     {
          logerror(_("Recv request header error: (%d) != (%d).\n"), ret, sizeof(request));
          goto clean;
     }


     // TODO: handler domain control
     switch (request.type)
     {
     case RQTYPE_DOMAIN_CONTROL:
          ret = hl_domain_control(g_c, infd, request.length);
          break;

     default:
          loginfo(_("unknown type %d\n"), request.type);
     }


clean:
     close(infd);
     return ret;
}


static int __register_node(CpConfig *C, int efd)
{
     loginfo(_("START register node\n"));

     int sfd = 0, ret = 0;
     int retry = 0;

     LyRequest header;
     header.type = RQTYPE_REGISTER;
     header.from = RQTARGET_COMPUTE;
     header.length = sizeof(ComputeNodeInfo);

     while(retry++ < REGISTER_RETRY_NUMBER)
     {
          loginfo(_("Sleep %d seconds before register.\n"), retry);
          sleep(retry);

          if (sfd <= 0)
          {
               sfd = connect_to_host(C->cts_ip, C->cts_port);
               if ( sfd <= 0 )
                    continue;
          }

          // Send request
          if (ly_send(sfd, &header, sizeof(LyRequest), 0, SEND_TIMEOUT))
               continue;

          if(ly_send(sfd, g_c->node, sizeof(ComputeNodeInfo), 0, SEND_TIMEOUT))
               continue;

          // Get respond
          LyRespond respond;
          if (ly_recv(sfd, &respond, sizeof(LyRespond), 0, RECV_TIMEOUT))
               continue;

          if (respond.status != RESPOND_STATUS_OK)
          {
               logerror(_("Register respond.status = %d\n"), respond.status);
               break;
          }

          struct epoll_event ev;
          ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP;
          ev.data.fd = sfd;
          ret = epoll_ctl(efd, EPOLL_CTL_ADD, sfd, &ev);
          if ( ret < 0)
          {
               logerror("Add keep alive to epoll error.\n");
               continue;
          } else {
               loginfo("Add keep alive to epoll success.\n");
               ret = 0;
               break;
          }

     }

     return ret;
}


int main (int argc, char *argv[])
{
     int ret;

     #define PACKAGE "luoyun"
     setlocale (LC_ALL, "");
     bindtextdomain (PACKAGE, LOCALEDIR);
     textdomain (PACKAGE);

     g_c = malloc( sizeof(CpConfig) );
     if (g_c == NULL)
     {
          printf(_("malloc for g_c have a error.\n"));
          return -1;
     }

     /* Init g_c */
     g_c->verbose = 0;
     g_c->daemon = 0;
     g_c->debug = 0;
     g_c->node = NULL;
     g_c->conn = NULL;
     *(g_c->host_ip) = '\0';
     g_c->host_port = 0;
     *(g_c->cts_ip) = '\0';
     g_c->cts_port = 0;

     sprintf(g_c->config, DEFAULT_CONFIG_PATH);
     sprintf(g_c->log, DEFAULT_LOG_PATH);
     sprintf(g_c->root_path, DEFAULT_ROOT_PATH);

     int optind;
     optind = parse_opt(argc, argv, g_c);
     if (optind == -1)
     {
          usage();
          return 0;
     } else if (optind < 0) {
          printf(_("parse options error.\n"));
          return -2;
     }

     // TODO: already_running();

     /* Daemonize the progress */
     if (g_c->daemon)
     {
          if (g_c->debug)
               lyu_daemonize(g_c->log, LYDEBUG);
          else
               lyu_daemonize(g_c->log, LYINFO);
     }

     /* Parse configure */
     if ( __parse_config( g_c ) )
          return -3;




     if (g_c->host_ip == NULL || g_c->host_port == 0)
     {
          logerror(_("host_ip or host_port have not set.\n"));
          return -3;
     }

     // Connect to libvirtd
     libvirtd_connect(g_c);

     // Init node info
     init_node_info(g_c);
     if (g_c->node == NULL)
          return -4;

     // Now, node is starting
     g_c->node->status = NODE_S_RUNNING;

     __print_config(g_c);


     // Fix Me: ip and port used by both g_sc and g_sc->node
     strcpy(g_c->node->ip, g_c->host_ip);
     g_c->node->port = g_c->host_port;

     print_node_info(g_c->node);


     int efd;
     efd = epoll_create(MAX_EVENTS);
     if (efd == -1)
     {
          perror("epoll_create");
          return -1;
     }
     struct epoll_event ev, events[MAX_EVENTS];

     /* Register node and keep alive */
     __register_node(g_c, efd);

     /* Create a socket and listen on it */
     char str_port[16];
     sprintf(str_port, "%d", g_c->host_port);
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

     ev.events = EPOLLIN | EPOLLET;
     ev.data.fd = listener;
     ret = epoll_ctl(efd, EPOLL_CTL_ADD, listener, &ev);
     if ( ret < 0)
     {
          logerror("Add listener to epoll error.\n");
          return -1;
     } else {
          loginfo("Add listener to epoll success.\n");
     }

     int n, i;

     while(1)
     {
          n = epoll_wait(efd, events, MAX_EVENTS, -1);
          for (i = 0; i < n; i++)
          {
               if (events[i].events & EPOLLRDHUP)
               {
                    logdebug(_("close by remote\n"));
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
                    /* New client comming in, new task */
                    //TODO: maybe use pthread do task
                    __new_client(listener, efd);
               }

               else {
                    logdebug(_("Have request, but I can not do now.\n"));
               }

          }
     }


     // TODO: clean everything
     free(g_c);
     return 0;
}
