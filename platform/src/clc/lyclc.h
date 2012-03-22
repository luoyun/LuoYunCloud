#ifndef __LY_INCLUDE_CLC_LYCLC_H
#define __LY_INCLUDE_CLC_LYCLC_H

#include "options.h"

#define CLC_EPOLL_TIMEOUT	1000 /* in ms */
#define CLC_MCAST_JOIN_INTERVAL 10 /* in seconds */
#define CLC_JOB_DISPATCH_INTERVAL 10
#define CLC_JOB_INTERNAL_INTERVAL 60

#define CLC_SOCKET_KEEPALIVE_INTVL  10
#define CLC_SOCKET_KEEPALIVE_PROBES 3

/* functions defined in mcast.c */
int ly_mcast_send_join(void);
int ly_clc_ip_get(void);
void ly_clc_ip_clean(void);

/* glocal var, defined in lyclc.c */
extern CLCConfig *g_c;

#endif
