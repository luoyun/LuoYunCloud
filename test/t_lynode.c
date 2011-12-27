#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h> /* gethostname */


#include "util/luoyun.h"


int main(int argc, char *argv[])
{
     if (argc < 5)
     {
          printf("Usage: %s ip port domain_id action\n", argv[0]);
          return -1;
     }

     DomainControlData dc;
     dc.id = atoi(argv[3]);
     dc.action = atoi(argv[4]);

     LyRequest request;
     request.type = RQTYPE_DOMAIN_CONTROL;
     request.from = RQTARGET_CONTROL;
     request.length = sizeof(dc);
     int sk, err;
     sk = connect_to_host(argv[1], atoi(argv[2]));

     err = send(sk, &request, sizeof(request), 0);
     if ( err == -1 )
     {
          printf("send error\n");
     }

     err = send(sk, &dc, sizeof(dc), 0);
     if ( err == -1 )
     {
          printf("send DomainControlData error\n");
     }

     close(sk);
          

     return 0;
}
