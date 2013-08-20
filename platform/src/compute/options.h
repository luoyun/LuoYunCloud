#ifndef __LY_INCLUDE_COMPUTE_OPTIONS_H
#define __LY_INCLUDE_COMPUTE_OPTIONS_H

#include "../luoyun/luoyun.h"

#define PROGRAM_NAME "lynode"
#define PROGRAM_VERSION VERSION

typedef enum CLC_Auto_Connect_t {
    UNKNOWN = 0,
    ALWAYS = 1,
    ONCE = 2,
    DISABLE = 3,
} CLC_Auto_Connect_Mode;

/*
** compute node configuration, populated based on lynode.conf and 
** command line option
*/
typedef struct NodeConfig_t {
    CLC_Auto_Connect_Mode auto_connect;
    char *clc_ip;          /* cloud controller ip */
    int  clc_port;         /* cloud controller port */
    char *clc_mcast_ip;    /* cloud controller mcast ip */
    int  clc_mcast_port;   /* cloud controller mcast port */
    char *node_data_dir;   /* compute node data directory */
    char *app_data_dir;    /* appliances sub-directory */
    char *ins_data_dir;    /* instances sub-directory */
    char *trash_data_dir;  /* trash data sub-directory */
    char *conf_path;       /* config file path */
    char *sysconf_path;    /* sysconf file path */
    char *log_path;        /* log file path */
    char *pid_path;        /* pid file path */
    char *osm_conf_path;   /* osmanage configuraton path inside instance */
    char *osm_key_path;    /* osmanage key file path inside instance */
    char *vm_template_path; /* vm xml template file path */
    char *vm_xml;          /* vm xml template */
    char *vm_template_net_nat_path;
    char *vm_xml_net_nat;
    char *vm_template_net_br_path;
    char *vm_xml_net_br;
    char *vm_template_disk_path;
    char *vm_xml_disk;
    char *net_primary;
    char *net_secondary;
    int  verbose;
    int  debug;
    int  daemon;
    int  driver;
} NodeConfig;

/*
** compute node dynamic configuration, populated based on lynode.sysconf
*/
typedef struct NodeSysConfig_t {
    char *clc_ip;     /* cloud controller ip */
    int  clc_port;    /* cloud controller port */
    int  node_tag;    /* node unique identifier */
    char * node_secret;	/* node secret, used for clc authentication */
} NodeSysConfig;

#define NODE_CONFIG_RET_HELP		1
#define NODE_CONFIG_RET_VER		2
#define NODE_CONFIG_RET_ERR_CMD          -1
#define NODE_CONFIG_RET_ERR_ERRCONF      -2
#define NODE_CONFIG_RET_ERR_NOCONF       -3
#define NODE_CONFIG_RET_ERR_CONF         -4
#define NODE_CONFIG_RET_ERR_NOMEM        -5
#define NODE_CONFIG_RET_ERR_UNKNOWN	-255
int node_config(int argc, char *argv[], NodeConfig *c, NodeSysConfig *s);

void usage(void);

#endif
