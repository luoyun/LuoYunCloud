#ifndef __LY_INCLUDE_CLC_OPTIONS_H
#define __LY_INCLUDE_CLC_OPTIONS_H

/* #include "../luoyun/luoyun.h" */

#define PROGRAM_NAME "lyclc"
#define PROGRAM_VERSION VERSION

/*
** clc configuration, populated based on lyclc.conf and 
** command line option
*/
typedef struct CLCConfig_t {
    char *clc_ip;            /* cloud controller ip */
    int   clc_port;          /* cloud controller port */
    char *clc_mcast_ip;      /* cloud controller mcast ip */
    int   clc_mcast_port;    /* cloud controller mcast port */
    char *clc_data_dir;          /* clc data dir */
    char *db_name;           /* db name, e.g. lyweb */
    char *db_user;           /* db user name */
    char *db_pass;           /* db user password */
    char *conf_path;         /* config file path */
    char *log_path;          /* log file path */
    char *pid_path;          /* pid file path */
    char *vm_name_prefix;    /* VM name prefix */
    int   node_select;
    int   node_storage_low;
    int   verbose;
    int   debug;
    int   daemon;
    int   node_cpu_factor, node_mem_factor;
} CLCConfig;

#define NODE_SELECT_ANY		0 
#define NODE_SELECT_LAST_ONLY	1

#define CLC_CONFIG_RET_HELP		1
#define CLC_CONFIG_RET_VER		2
#define CLC_CONFIG_RET_ERR_CMD		-1
#define CLC_CONFIG_RET_ERR_ERRCONF	-2
#define CLC_CONFIG_RET_ERR_NOCONF	-3
#define CLC_CONFIG_RET_ERR_CONF		-4
#define CLC_CONFIG_RET_ERR_NOMEM	-5
#define CLC_CONFIG_RET_ERR_UNKNOWN	-255
int clc_config(int argc, char *argv[], CLCConfig * c);
void usage(void);

/* retrieve/create clc uuid */
char * clc_uuid(CLCConfig * c);

#endif
