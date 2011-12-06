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
#include "compute/domain.h"
#include "compute/node.h"
#include "compute/handler.h"


#include "compute/server.h"

/* Parse the config file of compute server */
int
lyu_compute_server_config ( const char *file,
                            LyComputeServerConfig *sc )
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

          else if ( (kstr = strstr(line, "CONTROL_SERVER_IP")) != NULL )
               strcpy(sc->cts_ip, vstr);

          else if ( (kstr = strstr(line, "CONTROL_SERVER_PORT")) != NULL )
               sc->cts_port = atoi(vstr);

          else if ( (kstr = strstr(line, "ROOT_PATH")) != NULL )
               strcpy(sc->root_path, vstr);

          else
               logprintfl(LYERROR, _("Not support grammar: %s\n"), line);

     }

     return 0;
}

int
lyu_print_compute_server_config ( LyComputeServerConfig *sc )
{
     logsimple(
          "LyComputeServerConfig = {\n"
          "  host_ip = %s\n"
          "  host_port = %d\n"
          "  cts_ip = %s\n"
          "  cts_port = %d\n"
          "  root_path = %s\n"
          "  conn = %d\n"
          "  node = ...\n"
          "}\n",
          sc->host_ip, sc->host_port,
          sc->cts_ip, sc->cts_port,
          sc->root_path, sc->conn);

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
               update_compute_node_info(sc);
               timeout = 6;
          } else {
               sleep(1);
               timeout--;
          }
     }
     //pthread_exit((void *)0);
}


void *__request_handler (void *arg)
{
     LySockRequestHandler *RH;
     RH = (LySockRequestHandler *)arg;

     switch (RH->request->action) {

     case LA_DOMAIN_RUN:
     case LA_DOMAIN_STOP:
     case LA_DOMAIN_SUSPEND:
     case LA_DOMAIN_SAVE:
     case LA_DOMAIN_REBOOT:
          hl_control_domain(g_sc, RH);
          break;
                    
     default:
          logprintfl(LYERROR, "Unknown request action: %d\n",
                     RH->request->action);
     }


     close(RH->sk);
     free(RH->request);
     free(RH);

     pthread_exit((void *)0);
}


int main (int argc, char *argv[])
{

#if 0
     if ( argc < 3 )
     {
          printf("Usage: %s IP PORT\n", argv[0]);
          return -1;
     }
#endif
     // TODO: already_running();


     /* Parse configure */
     g_sc = malloc( sizeof(LyComputeServerConfig) );
     if (g_sc == NULL)
     {
          logprintfl(LYERROR, "g_sc malloc error.\n");
          return -2;
     }
     *g_sc->host_ip = '\0';
     g_sc->host_port = 0;
     *g_sc->cts_ip = '\0';
     g_sc->cts_port = 0;
     *g_sc->root_path = '\0';
     g_sc->conn = NULL;
     g_sc->node = NULL;
     const char *c_file = "/etc/LuoYun/compute_server.conf";
     lyu_compute_server_config( c_file, g_sc );

     if ( g_sc->host_ip == NULL ||
          g_sc->host_port == 0 )
     {
          logprintfl(LYDEBUG, "compute_config file error.\n");
          return -3;
     }

     if ( *(g_sc->root_path) == '\0' )
          sprintf(g_sc->root_path, "/opt/LuoYun_Node/");

     libvirtd_connect(g_sc);

     init_node_info(g_sc);
     if (g_sc->node == NULL)
          return -4;

     // Now, node is starting
     g_sc->node->status = NODE_S_RUNNING;

     lyu_print_compute_server_config(g_sc);

     // Fix Me: ip and port used by both g_sc and g_sc->node
     strcpy(g_sc->node->ip, g_sc->host_ip);
     g_sc->node->port = g_sc->host_port;
     print_node_info(g_sc->node);

     /* TODO: Test control server is alive ? */

     /* Run __update_status_manager thread */
     pthread_t update_manager_tid;
     pthread_create(&update_manager_tid, NULL, __update_status_manager, g_sc);


     /* Daemonize the progress */
     //lyu_daemonize("/tmp/control.log");


     /* Create a socket and listen on it */
     // TODO: ugly listen on socket.
     char service[30];
     sprintf(service, "%d", g_sc->host_port);
     int sfd;
     sfd = create_socket(g_sc->host_ip, service);


     int nsfd; /* new socket connect */
     struct sockaddr nskaddr;
     struct sockaddr_in *nskaddr_in;
     socklen_t size_skaddr = sizeof(struct sockaddr);


     LySockRequest *request;
     LySockRequestHandler *RH;
     pthread_t handler_tid;
     int recvlen;

     for (;;)
     {
          nsfd = accept(sfd, &nskaddr, &size_skaddr);
          if ( nsfd < 0 )
          {
               // TODO:
               logprintfl(LYERROR, "accept error.\n");
               sleep(1);
               continue;
          }

          nskaddr_in = (struct sockaddr_in *)&nskaddr;
          logprintfl(LYDEBUG, "FROM: %s:%d\n",
                     inet_ntoa(nskaddr_in->sin_addr),
                     ntohs(nskaddr_in->sin_port));

          request = malloc( sizeof(LySockRequest) );
          if (request == NULL)
          {
               logprintfl(LYERROR, "%s: malloc error, "
                          "close connect\n", __func__);
               close(nsfd);
               continue;
          }

          recvlen = recv(nsfd, request,
                         sizeof(LySockRequest), 0);
          if ( recvlen != sizeof(LySockRequest) )
          {
               logprintfl(LYERROR, "read request error.\n");
               close(nsfd);
               continue;
          }

          logprintfl(LYDEBUG, "request = { "
                     "form = %d, to = %d, type = %d, "
                     "action = %d, datalen = %d }\n",
                     request->from, request->to,
                     request->type, request->action,
                     request->datalen);

          RH = malloc( sizeof(LySockRequestHandler) );
          if (RH == NULL)
          {
               logprintfl(LYERROR, "%s: malloc RH err, "
                          "close connect.\n", __func__);
               close(nsfd);
               continue;
          }

          RH->request = request;
          RH->sk = nsfd;

          pthread_create(&handler_tid, NULL,
                         __request_handler, RH);
     }

     close(sfd);
     return 0;
}
