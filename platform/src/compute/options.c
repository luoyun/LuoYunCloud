/*
** Copyright (C) 2012 LuoYun Co. 
**
**           Authors:
**                    lijian.gnu@gmail.com 
**                    zengdongwu@hotmail.com
**  
** This program is free software; you can redistribute it and/or modify
** it under the terms of the GNU General Public License as published by
** the Free Software Foundation; either version 2 of the License, or
** (at your option) any later version.
**  
** This program is distributed in the hope that it will be useful,
** but WITHOUT ANY WARRANTY; without even the implied warranty of
** MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
** GNU General Public License for more details.
**  
** You should have received a copy of the GNU General Public License
** along with this program; if not, write to the Free Software
** Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
**  
*/
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>

#include "../util/logging.h"
#include "../util/misc.h"
#include "../util/lyutil.h"
#include "options.h"

#define UNDEFINED_CFG_INT (-1)

#define GETOPT_HELP_OPTION_DECL                 \
     "help", no_argument, NULL, 'h'
#define GETOPT_VERSION_OPTION_DECL              \
     "version", no_argument, NULL, 'V'

// Flag set by '--verbose'
static int verbose_flag = 0;

static struct option const long_opts[] = {
    {"verbose", no_argument, &verbose_flag, 1},
    {"brief", no_argument, &verbose_flag, 0},

    {"debug", no_argument, NULL, 'd'},
    {"daemon", no_argument, NULL, 'D'},
    {"config", required_argument, NULL, 'c'},
    {"log", required_argument, NULL, 'l'},
    {GETOPT_HELP_OPTION_DECL},
    {GETOPT_VERSION_OPTION_DECL},
    {NULL, 0, NULL, 0}
};

/*
** return --
** 0: normal
** 1: usage 
** 2: version
** negative number: error
*/
static int __parse_opt(int argc, char *argv[], NodeConfig * c)
{
    int ret = 0, opt = 0;
    const char *const short_options = "c:hdDl:V";

    while (1) {
        // getopt_long stores the option index here.
        int option_index = 0;

        opt = getopt_long(argc, argv, short_options,
                          long_opts, &option_index);

        if (opt == -1)
            break;

        switch (opt) {
        case 0:
            /* continue */
            break;

        case 'c':
            c->conf_path = strdup(optarg);
            if (c->conf_path == NULL)
                return NODE_CONFIG_RET_ERR_NOMEM;
            break;

        case 'l':
            c->log_path = strdup(optarg);
            if (c->log_path == NULL)
                return NODE_CONFIG_RET_ERR_NOMEM;
            break;

        case 'h':
            ret = NODE_CONFIG_RET_HELP;
            break;

        case 'd':
            c->debug = 1;
            break;

        case 'D':
            c->daemon = 1;
            break;

        case 'V':
            ret = NODE_CONFIG_RET_VER;
            break;

        default:
            ret = -1;
            break;
        }
    }
    c->verbose = verbose_flag;

    if (optind < argc) {
        logsimple("%s: non-option ARGV-elements: ", argv[0]);
        while (optind < argc)
            logsimple("%s ", argv[optind++]);
        logsimple("\n");
        ret = NODE_CONFIG_RET_ERR_CMD;
    }

    return ret;
}

#include <path_utils.h>
#include <collection_tools.h>
#include <ini_config.h>

/* *v == NULL require space to be allocated */
static int __parse_oneitem_str(const char *k, char **v, int vlen, struct collection_item *ini)
{
    struct collection_item *item;
    int error;

    if (get_config_item(NULL, k, ini, &item)) {
        logsimple(_("error reading value for %s\n"), k);
        return NODE_CONFIG_RET_ERR_CONF;
    }
    else {
        if (!item)
            return 0;

        const char *s = get_const_string_config_value(item, &error);
        if (error) {
            logsimple(_("error getting %s\n"), k);
            return NODE_CONFIG_RET_ERR_CONF;
        }

        if (s == NULL || strlen(s) == 0)
            *v = NULL;
        else if (*v == NULL) {
            *v = strdup(s);
            if (*v == NULL)
                return NODE_CONFIG_RET_ERR_NOMEM;
        }
        else
            strncpy(*v, s, vlen);
    }

    return 0;
}

static int __parse_oneitem_int(const char *k, int *v, struct collection_item *ini)
{
    struct collection_item *item;
    int error;

    if (get_config_item(NULL, k, ini, &item)) {
        logsimple(_("error reading value for %s\n"), k);
        return NODE_CONFIG_RET_ERR_CONF;
    }
    else {
        if (!item)
            return 0;

        *v = get_int_config_value(item,1, 10, &error);
        if (error) {
            logsimple(_("error getting %s\n"), k);
            return NODE_CONFIG_RET_ERR_CONF;
        }
    }

    return 0;
}

static int __parse_config(NodeConfig *c)
{
    if (c == NULL)
        return NODE_CONFIG_RET_ERR_UNKNOWN;

    if (file_not_exist(c->conf_path))
        return NODE_CONFIG_RET_ERR_NOCONF;

    struct collection_item *ini_config = NULL;
    struct collection_item *error_set = NULL;
 
    if (config_from_file(PROGRAM_NAME, c->conf_path,
                             &ini_config, INI_STOP_ON_ANY, &error_set)){
        logsimple(_("error while reading %s\n"), c->conf_path);
        return NODE_CONFIG_RET_ERR_CONF;
    }

    char * driver = NULL;
    char * auto_connect = NULL;
    if (__parse_oneitem_str("LYNODE_SYSCONF_PATH", &c->sysconf_path, 
                             0, ini_config) || 
        __parse_oneitem_str("LYNODE_DRIVER", &driver, 
                             0, ini_config) || 
        __parse_oneitem_str("LYCLC_AUTO_CONNECT", &auto_connect, 
                             0, ini_config) || 
        __parse_oneitem_str("LYCLC_HOST", &c->clc_ip,
                             0, ini_config) || 
        __parse_oneitem_int("LYCLC_PORT", &c->clc_port, 
                             ini_config) || 
        __parse_oneitem_str("LYCLC_MCAST_IP", &c->clc_mcast_ip, 
                             0, ini_config) || 
        __parse_oneitem_int("LYCLC_MCAST_PORT", &c->clc_mcast_port, 
                             ini_config) || 
        __parse_oneitem_str("LYOSM_CONF_PATH", &c->osm_conf_path,
                             0, ini_config) || 
        __parse_oneitem_str("LYOSM_KEY_PATH", &c->osm_key_path,
                             0, ini_config) || 
        __parse_oneitem_str("LYNODE_DATA_DIR", &c->node_data_dir, 
                             0, ini_config))
        return NODE_CONFIG_RET_ERR_CONF;

    /* value conversion */
    if (driver != NULL) {
        if (strcasecmp(driver, "KVM") == 0)
            c->driver = HYPERVISOR_IS_KVM;
        else if (strcasecmp(driver, "XEN") == 0)
            c->driver = HYPERVISOR_IS_XEN;
        else
            c->driver = HYPERVISOR_IS_UNKNOWN;
        free(driver);
    }
    if (auto_connect != NULL) {
        if (strcasecmp(auto_connect, "ALWAYS") == 0)
            c->auto_connect = ALWAYS;
        else if (strcasecmp(auto_connect, "ONCE") == 0)
            c->auto_connect = ONCE;
        else if (strcasecmp(auto_connect, "DISABLE") == 0)
            c->auto_connect = DISABLE;
        else {
            logsimple(_("unrecognized value for LYCLC_AUTO_CONNECT %s\n"), auto_connect);
            return NODE_CONFIG_RET_ERR_CONF;
        }
        free(auto_connect);
    }
    if (c->daemon == UNDEFINED_CFG_INT) {
        if (__parse_oneitem_int("LYNODE_DAEMON", &c->daemon, ini_config))
            return NODE_CONFIG_RET_ERR_CONF;
    }
    if (c->debug == UNDEFINED_CFG_INT) {
        if (__parse_oneitem_int("LYNODE_DEBUG", &c->debug, ini_config))
            return NODE_CONFIG_RET_ERR_CONF;
    }
    if (c->log_path == NULL) {
        if (__parse_oneitem_str("LYNODE_LOG_PATH", &c->log_path, 0, ini_config))
            return NODE_CONFIG_RET_ERR_CONF;
    }

    if (ini_config) 
        free_ini_config(ini_config);
 
    if (error_set)
        free_ini_config_errors(error_set);

    return 0;
}

static int __parse_sysconf(char *path, NodeSysConfig *s)
{
    if (s == NULL)
        return NODE_CONFIG_RET_ERR_UNKNOWN;

    if (file_not_exist(path))
        return 0;

    struct collection_item *ini_config = NULL;
    struct collection_item *error_set = NULL;

    if (config_from_file(PROGRAM_NAME, path,
                         &ini_config, INI_STOP_ON_ANY, &error_set)){
        logsimple(_("error while reading %s\n"), path);
        return NODE_CONFIG_RET_ERR_CONF;
    }

    if (__parse_oneitem_str("LYCLC_HOST", &s->clc_ip,
                             0, ini_config) ||
        __parse_oneitem_int("LYCLC_PORT", &s->clc_port,
                             ini_config) ||
        __parse_oneitem_int("LYNODE_TAG", &s->node_tag,
                             ini_config) ||
        __parse_oneitem_str("LYNODE_SECRET", &s->node_secret,
                             0, ini_config))
        return NODE_CONFIG_RET_ERR_CONF;

    if (ini_config)
        free_ini_config(ini_config);

    if (error_set)
        free_ini_config_errors(error_set);

    return 0;
}

#include <arpa/inet.h>
static int __is_IP_valid(char *ip, int mcast)
{
    if (ip == NULL)
        return 0;

    struct sockaddr_in sa;
    int ret = inet_pton(AF_INET, ip, &(sa.sin_addr));
    if (ret <= 0)
        return 0;
    else
        ret = 1;
    if (mcast)
        ret = (ntohl(sa.sin_addr.s_addr) & 0xf0000000) == 0xe0000000 ? 1 : 0;
    return ret;
}

static int __is_port_valid(int port)
{
    if (port <= 1024 || port > 65535)
        return 0;
    return 1;
}

#include <sys/types.h>
#include <dirent.h>
#include <unistd.h>
static int __clean_lockfile(char * path)
{
    if (chdir(path))
        return -1;

    DIR * d = opendir(".");
    if (d == NULL)
        return -1;

    struct dirent * r = readdir(d);
    while (r) {
        if (strncmp(r->d_name, ".forlock", 8) == 0) {
            if (unlink(r->d_name))
                return -1;
        }
        r = readdir(d);
    }

    closedir(d);
    return 0;
}

void usage(void)
{

    printf(_("\
%s is the compute node of LuoYun Cloud Platform.\n\n\
"), PROGRAM_NAME);

    printf(_("\
Usage : %s [OPTION]\n\n\
"), PROGRAM_NAME);

    printf(_("  -c, --config    Specify the config file\n"
             "                  default is " DEFAULT_LYNODE_CONF_PATH " \n"
             "  -l, --log       log file, must be full path\n"
             "                  default is " DEFAULT_LYNODE_LOG_PATH " \n"
             "  -D, --daemon    run as a daemon\n"
             "  -d, --debug     debug mode\n"
             "  --verbose       verbose or\n"
             "  --brief         brief logging\n"));

}

int node_config(int argc, char *argv[], NodeConfig *c, NodeSysConfig *s)
{
    int ret;

    if (c == NULL)
        return NODE_CONFIG_RET_ERR_UNKNOWN; /* internal error */

    /* initialize NodeConfig with undefined values */
    bzero(c, sizeof(NodeConfig));
    c->auto_connect = UNKNOWN;
    c->verbose = UNDEFINED_CFG_INT;
    c->daemon = UNDEFINED_CFG_INT;
    c->debug = UNDEFINED_CFG_INT;
    c->driver = HYPERVISOR_IS_KVM;

    /* parse command line options */
    ret = __parse_opt(argc, argv, c);
    if (ret)
        return ret; /* to exit program */

    /* check conf_path before reading it */
    if (c->conf_path == NULL) {
        c->conf_path = strdup(DEFAULT_LYNODE_CONF_PATH);
        if (c->conf_path == NULL)
            return NODE_CONFIG_RET_ERR_NOMEM;
    }
    
    /* parse config file */
    if (access(c->conf_path, R_OK)) {
        ret = __parse_config(c);
        if (ret && ret != NODE_CONFIG_RET_ERR_NOCONF)
            return ret; /* to exit programe */
    }

    /* set default values for auto_connect */
    if (c->auto_connect == UNKNOWN)
        c->auto_connect = ALWAYS;

    /* read sysconf settings */
    bzero(s, sizeof(NodeSysConfig));
    s->node_tag = -1;
    if (c->sysconf_path == NULL) {
        c->sysconf_path = strdup(DEFAULT_LYNODE_SYSCONF_PATH);
        if (c->conf_path == NULL)
            return NODE_CONFIG_RET_ERR_NOMEM;
    }
    if (access(c->sysconf_path, W_OK) != 0) {
        if (lyutil_create_file(c->sysconf_path, 0) < 0) {
            logsimple(_("not able to write to %s\n"), c->sysconf_path);
            return NODE_CONFIG_RET_ERR_CMD;
        }
    }
    else {
        ret = __parse_sysconf(c->sysconf_path, s);
        if (ret)
           return ret; /* to exit program */
    }

    /* set default values for unconfigured settings */
    if (c->verbose == UNDEFINED_CFG_INT)
        c->verbose = 0;
    if (c->daemon == UNDEFINED_CFG_INT)
        c->daemon = 1;
    if (c->debug == UNDEFINED_CFG_INT)
        c->debug = 0;
    if (c->clc_port == 0)
        c->clc_port = DEFAULT_LYCLC_PORT;
    if (c->clc_mcast_ip == NULL)
        c->clc_mcast_ip = strdup(DEFAULT_LYCLC_MCAST_IP);
    if (c->clc_mcast_port == 0)
        c->clc_mcast_port = DEFAULT_LYCLC_MCAST_PORT;
    if (c->log_path == NULL) {
        c->log_path = strdup(DEFAULT_LYNODE_LOG_PATH);
        if (c->conf_path == NULL)
            return NODE_CONFIG_RET_ERR_NOMEM;
    }
    if (c->osm_conf_path == NULL) {
        c->osm_conf_path = strdup(DEFAULT_LYOSM_CONF_PATH);
        if (c->osm_conf_path == NULL)
            return NODE_CONFIG_RET_ERR_NOMEM;
    }
    if (c->osm_key_path == NULL) {
        c->osm_key_path = strdup(DEFAULT_LYOSM_KEY_PATH);
        if (c->osm_key_path == NULL)
            return NODE_CONFIG_RET_ERR_NOMEM;
    }
    if (c->node_data_dir == NULL) {
        c->node_data_dir = strdup(DEFAULT_LYNODE_DATA_DIR);
        if (c->node_data_dir == NULL)
            return NODE_CONFIG_RET_ERR_NOMEM;
    }

    /* create necessary sub-directories for normal operation */
    char path[PATH_MAX];
    if (snprintf(path, PATH_MAX, "%s/appliances", c->node_data_dir) >= PATH_MAX)
        return NODE_CONFIG_RET_ERR_CONF;
    if (lyutil_create_dir(path) != 0) {
        logsimple(_("failed creating directory of %s\n"), path);
        return NODE_CONFIG_RET_ERR_CMD;
    }
    if (__clean_lockfile(path) != 0) {
        logsimple(_("failed cleaning directory of %s\n"), path);
        return NODE_CONFIG_RET_ERR_CMD;
    }
    if (snprintf(path, PATH_MAX, "%s/instances", c->node_data_dir) >= PATH_MAX)
        return NODE_CONFIG_RET_ERR_CONF;
    if (lyutil_create_dir(path) != 0) {
        logsimple(_("failed creating directory of %s\n"), path);
        return NODE_CONFIG_RET_ERR_CMD;
    }
    if (__clean_lockfile(path) != 0) {
        logsimple(_("failed cleaning directory of %s\n"), path);
        return NODE_CONFIG_RET_ERR_CMD;
    }

    /* simple configuration validity checking */
    if (__is_IP_valid(c->clc_mcast_ip, 1) == 0) {
        logsimple(_("cloud controller mcast ip is invalid\n"));
        return NODE_CONFIG_RET_ERR_CONF;
    }
    if (__is_port_valid(c->clc_mcast_port) == 0 ) {
        logsimple(_("cloud controller port is invalid\n"));
        return NODE_CONFIG_RET_ERR_CONF;
    }
    if (__is_port_valid(c->clc_port) == 0 ) {
        logsimple(_("cloud controller port is invalid\n"));
        return NODE_CONFIG_RET_ERR_CONF;
    }
    if ((c->auto_connect == DISABLE || c->clc_ip)
        && __is_IP_valid(c->clc_ip, 0) == 0) {
        logsimple(_("cloud controller ip is invalid<%s>\n"), c->clc_ip);
        return NODE_CONFIG_RET_ERR_CONF;
    }
    if (c->log_path) {
        if (access(c->log_path, F_OK) && lyutil_create_file(c->log_path, 0) < 0) {
            logsimple(_("not able to create %s\n"), c->log_path);
            return NODE_CONFIG_RET_ERR_CMD;
        }
        if (access(c->log_path, W_OK)) {
            logsimple(_("not able to write to %s\n"), c->log_path);
            return NODE_CONFIG_RET_ERR_CMD;
        }
    }
    return ret;
}
