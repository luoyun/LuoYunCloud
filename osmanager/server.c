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
#include "osmanager/server.h"

/* global queue */
LyOsManagerConfig *g_sc = NULL;


/* Parse the config file of compute server */
int
__parse_config ( const char *file,
                       LyOsManagerConfig *sc )
{
     FILE *fp;
     char line[LINE_MAX];
     char *kstr; /* point to the key string */
     char *vstr; /* point to the value string */

     fp = fopen(file, "r");
     if ( fp == NULL )
     {
          logprintfl(LYERROR,
                     _("Can not open config file: %s\n"),
                     file);
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

          if ( (kstr = strstr(line, "CONTROL_SERVER_IP")) != NULL )
               strcpy(sc->cts_ip, vstr);

          else if ( (kstr = strstr(line, "CONTROL_SERVER_PORT")) != NULL )
               sc->cts_port = atoi(vstr);

          else if ( (kstr = strstr(line, "DOMAIN_ID")) != NULL )
               sc->domain_id = atoi(vstr);

          else if ( (kstr = strstr(line, "NODE_ID")) != NULL )
               sc->node_id = atoi(vstr);

          else
               logprintfl(LYERROR, _("Not support grammar: %s\n"), line);

     }

     return 0;
}




int
__print_config ( LyOsManagerConfig *sc )
{
     logsimple(
          "LyOsManagerConfig = {\n"
          "  host_ip = %s\n"
          "  host_port = %d\n"
          "  cts_ip = %s\n"
          "  cts_port = %d\n"
          "  domain_id = %d\n"
          "  node_id = %d\n"
          "}\n",
          sc->host_ip, sc->host_port,
          sc->cts_ip, sc->cts_port,
          sc->domain_id, sc->node_id);

     return 0;
}



int update_os_info (LyOsManagerConfig *sc)
{
     int sk, err;

     sk = connect_to_host(sc->cts_ip, sc->cts_port);
     if ( sk <= 0 ) return -1;

     // TODO: would be change to VosInfo !!!
     DomainInfo di;
     di.status = DOMAIN_S_RUNNING;
     di.id = sc->domain_id;
     di.node = sc->node_id;
     strcpy(di.ip, sc->host_ip);
     time(&di.updated);

     LySockRequest request;
     request.from = LST_VOS_S;
     request.to = LST_CONTROL_S;
     request.type = 0;
     request.action = LA_DOMAIN_STATUS;
     request.datalen = sizeof(DomainInfo);

     err = send(sk, &request, sizeof(LySockRequest), 0);
     err += send(sk, &di, sizeof(DomainInfo), 0);

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

     LyOsManagerConfig *sc;
     sc = (LyOsManagerConfig *)arg;

     int timeout = 0;
     for(;;)
     {
          if ( !timeout )
          {
               logprintfl(LYDEBUG, "OsManager: update status\n");
               update_os_info(sc);
               timeout = 6;
          } else {
               sleep(1);
               timeout--;
          }
     }

     //pthread_exit((void *)0);
}

int main (int argc, char *argv[])
{
     if ( argc < 3 )
     {
          printf("Usage: %s IP PORT\n", argv[0]);
          return -1;
     }

     // TODO: already_running();


     /* Parse configure */
     g_sc = malloc( sizeof(LyOsManagerConfig) );
     if (g_sc == NULL)
     {
          logprintfl(LYERROR, "%s: g_sc malloc error.\n",
                     __func__);
          return -2;
     }
     *g_sc->cts_ip = '\0';
     g_sc->cts_port = 0;
     strcpy(g_sc->host_ip, argv[1]);
     g_sc->host_port = atoi(argv[1]);

     const char *c_file = "/LuoYun/LuoYun.conf";
     __parse_config( c_file, g_sc );

     /* Daemonize the progress */
     lyu_daemonize("/tmp/osmanager.log");

     __print_config(g_sc);

     /* Run __update_status_manager thread */
     pthread_t update_manager_tid;
     pthread_create(&update_manager_tid, NULL, __update_status_manager, g_sc);


     /* Create a socket and listen on it */
     // TODO: ugly listen on socket.
     int sfd;
     sfd = create_socket(argv[1], argv[2]);


     int nsfd; /* new socket connect */
     struct sockaddr nskaddr;
     struct sockaddr_in *nskaddr_in;
     socklen_t size_skaddr = sizeof(struct sockaddr);


     LySockRequest *request;
     LySockRequestHandler *RH;
     //pthread_t handler_tid;
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

          //pthread_create(&handler_tid, NULL,
          //               __request_handler, RH);
          close(nsfd);
     }

     close(sfd);
     return 0;
}
