#ifndef __LUOYUN_INCLUDE_compute_options_H
#define __LUOYUN_INCLUDE_compute_options_H

#include "util/luoyun.h"

#define DOMAIN_CONFIG_URI_TEMP "http://luoyun.co/instance/%d/config"

#define OS_DISK_FILE_GZ "os.img.gz"
#define OS_DISK_FILE "os.img"
#define LIBVIRTD_CONFIG "domain_libvirtd.xml"
#define DOMAIN_CONFIG_FILE "domain.conf"

/* compute node config */
#include <libvirt/libvirt.h>
typedef struct CpConfig_t {
     char host_ip[MAX_IP_LEN];
     int  host_port;
     char cts_ip[MAX_IP_LEN]; /* control server ip */
     int  cts_port;           /* control server port */
     char root_path[MAX_PATH_LEN];

     /* Needed init by step */
     virConnectPtr conn;     /* libvirtd_connect() */
     ComputeNodeInfo *node;  /* init_node_info() */

     char config[LINE_MAX]; /* Config file path */
     char log[LINE_MAX];    /* log file path */
     char verbose;
     char debug;
     char daemon;
} CpConfig;



int parse_opt(int argc, char *argv[], CpConfig *c);



#endif /* End __LUOYUN_INCLUDE_compute_options_H */
