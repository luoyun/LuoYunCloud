#ifndef __LUOYUN_INCLUDE_COMPUTE_SERVER_H
#define __LUOYUN_INCLUDE_COMPUTE_SERVER_H


#include <libvirt/libvirt.h>
typedef struct LyComputeServerConfig_t {
     char host_ip[MAX_IP_LEN];
     int  host_port;
     char cts_ip[MAX_IP_LEN]; /* control server ip */
     int cts_port;            /* control server port */
     char root_path[MAX_PATH_LEN];

     /* Needed init by step */
     virConnectPtr conn;     /* libvirtd_connect() */
     ComputeNodeInfo *node;  /* init_node_info() */
} LyComputeServerConfig;




#endif /* End __LUOYUN_INCLUDE_COMPUTE_SERVER_H */
