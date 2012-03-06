#ifndef __LY_INCLUDE_CLC_LYCLC_H
#define __LY_INCLUDE_CLC_LYCLC_H

#include "options.h"

#define CLC_EPOLL_TIMEOUT	1000 /* in ms */
#define CLC_MCAST_JOIN_TIMEOUT	5000
#define CLC_MCAST_JOIN_INTERVAL (CLC_MCAST_JOIN_TIMEOUT/CLC_EPOLL_TIMEOUT)
#define CLC_JOB_DISPATCH_TIMEOUT 1000
#define CLC_JOB_DISPATCH_INTERVAL (CLC_JOB_DISPATCH_TIMEOUT/CLC_EPOLL_TIMEOUT)

#define CLC_SOCKET_KEEPALIVE_INTVL  10
#define CLC_SOCKET_KEEPALIVE_PROBES 3

/* functions defined in mcast.c */
int ly_mcast_send_join(void);
int ly_clc_ip_get(void);
void ly_clc_ip_clean(void);

/* glocal var, defined in lyclc.c */
extern CLCConfig *g_c;

#endif
