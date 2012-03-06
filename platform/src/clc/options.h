#ifndef __LY_INCLUDE_CLC_OPTIONS_H
#define __LY_INCLUDE_CLC_OPTIONS_H

#include "../luoyun/luoyun.h"

#define PROGRAM_NAME "lyclc"
#define PROGRAM_VERSION VERSION

/*
** clc configuration, populated based on lyclc.conf and 
** command line option
*/
typedef struct CLCConfig_t {
    char clc_ip[MAX_IP_LEN];    /* cloud controller ip */
    int clc_port;               /* cloud controller port */
    char clc_mcast_ip[MAX_IP_LEN];      /* cloud controller mcast ip */
    int clc_mcast_port;         /* cloud controller mcast port */
    char *db_name;              /* db name, e.g. lyweb */
    char *db_user;              /* db user name */
    char *db_pass;              /* db user password */
    char *conf_path;            /* config file path */
    char *log_path;             /* log file path */
    int verbose;
    int debug;
    int daemon;
} CLCConfig;


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
