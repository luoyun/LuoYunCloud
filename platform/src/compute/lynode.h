#ifndef __LY_INCLUDE_COMPUTE_LYNODE_H
#define __LY_INCLUDE_COMPUTE_LYNODE_H

#include <libvirt/libvirt.h>
#include "../util/lypacket.h"
#include "../util/lyauth.h"
#include "options.h"

#define LY_NODE_EPOLL_WAIT 10000
#define LY_NODE_STOP_INSTANCE_WAIT 60
#define LY_NODE_START_INSTANCE_WAIT 20
#define LY_NODE_REBOOT_INSTANCE_WAIT 10
#define LY_NODE_THREAD_MAX 100
#define LY_NODE_LOAD_MAX   2000
#define LY_NODE_KEEPALIVE_INTVL  10
#define LY_NODE_KEEPALIVE_PROBES 3

typedef struct NodeControl_t {
    /* node configuration */
    NodeConfig config;

    /* node dynamic configuration */
    NodeSysConfig config_sys;

    /* node authentication configuration */
    AuthConfig auth;

    /* tracking node state */
    int state;

    /* clc ip/port being used */
    char * clc_ip;
    int    clc_port;
    char * node_ip;

    /* node info shared with clc */
    NodeInfo * node;

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
} NodeControl;

int ly_sysconf_save(void);

extern NodeControl * g_c;

#endif
