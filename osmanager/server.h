#ifndef __LUOYUN_INCLUDE_osmanager_server_H
#define __LUOYUN_INCLUDE_osmanager_server_H

typedef struct LyOsManagerConfig_t {
     char cts_ip[MAX_IP_LEN]; /* control server ip */
     int cts_port;            /* control server port */
     int domain_id;           /* domain id in DB */
     int node_id;             /* node id in DB */
     char host_ip[MAX_IP_LEN];
     int host_port;
     char host_mac[MAX_MAC_LEN];
} LyOsManagerConfig;



#endif /* End __LUOYUN_INCLUDE_osmanager_server_H */
