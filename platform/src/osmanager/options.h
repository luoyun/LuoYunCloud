#ifndef __LY_INCLUDE_OSMANAGER_OPTIONS_H
#define __LY_INCLUDE_OSMANAGER_OPTIONS_H

#include "osmlog.h"

typedef struct OSMConfig_t {
    char *clc_ip;          /* cloud controller ip */
    int   clc_port;        /* cloud controller port */
    char *clc_mcast_ip;    /* cloud controller mcast ip */
    int   clc_mcast_port;  /* cloud controller mcast port */
    int   osm_tag;         /* unique id on clc */
    char *osm_secret;      /* secret to authenticate clc */
    char *conf_path;       /* configuration file */
    char *scripts_dir;     /* dir of external scripts */
    char *key_path;        /* key file path */
    char *storage_ip;      /* storage server ip */
    int   storage_method;  /* storage method, NFS, ISCSI, etc */
    char *storage_parm;      /* storage parameters */
    char *log_path;        /* log file path */
    int   verbose;
    int   debug;
    int   daemon;
} OSMConfig;

#define OSM_CONFIG_RET_HELP		1
#define OSM_CONFIG_RET_VER		2
#define OSM_CONFIG_RET_ERR_CMD          -1
#define OSM_CONFIG_RET_ERR_ERRCONF      -2
#define OSM_CONFIG_RET_ERR_NOCONF       -3
#define OSM_CONFIG_RET_ERR_CONF         -4
#define OSM_CONFIG_RET_ERR_NOMEM        -5
#define OSM_CONFIG_RET_ERR_UNKNOWN	-255
int osm_config(int argc, char *argv[], OSMConfig *c);

void usage(void);

#endif
