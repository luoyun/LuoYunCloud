#ifndef __LY_INCLUDE_OSMANAGER_OSMANAGER_H
#define __LY_INCLUDE_OSMANAGER_OSMANAGER_H

#include "options.h"
#include "lyauth.h"
#include "lypacket.h"

#define LY_OSM_EPOLL_WAIT 10000

typedef struct OSMControl_t {
    /* osm configuration */
    OSMConfig config;

    /* node authentication configuration */
    AuthConfig auth;

    /* tracking node state */
    int state;

    /* clc ip/port being used */
    char * clc_ip;
    int    clc_port;
    char * osm_ip;

    /* epoll file descriptors */
    int efd;  /* event pool */
    int mfd;  /* mcast socket */
    int wfd;  /* work socket */

    /* per socket packet receive struct */
    LYPacketRecv mfd_pkt;  /* mcast socket packet */
    LYPacketRecv wfd_pkt;  /* work socket packet */

    /* control message buffer for mcast socket */
    char * mfd_cmsg;
    unsigned int mfd_cmsg_size;
} OSMControl;

extern OSMControl * g_c;

#define LY_SAFE_FREE(p) { if(p) free(p); p = NULL; }

#endif
