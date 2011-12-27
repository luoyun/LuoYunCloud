#ifndef __LUOYUN_INCLUDE_compute_lynode_H
#define __LUOYUN_INCLUDE_compute_lynode_H


#define PROGRAM_NAME "lynode"
#define PROGRAM_VERSION "0.1"

#define REGISTER_RETRY_NUMBER 100
#define REGISTER_RETRY_WAIT_ONE 1
#define REGISTER_RETRY_WAIT_TWO 5
#define REGISTER_RETRY_WAIT_THREE 20
#define REGISTER_RETRY_WAIT_FOUR 60

#define DEFAULT_CONFIG_PATH "/etc/LuoYun/lynode.conf"
#define DEFAULT_LOG_PATH "/var/log/lynode.log"
#define DEFAULT_ROOT_PATH "/opt/LuoYun_Node/"


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




#endif /* End __LUOYUN_INCLUDE_compute_lynode_H */
