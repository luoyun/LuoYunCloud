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

static int verbose_flag = 0;
static int debug_flag = UNDEFINED_CFG_INT;
static int daemon_flag = UNDEFINED_CFG_INT;

static struct option const long_opts[] = {
    {"verbose", no_argument, &verbose_flag, 1},
    {"brief", no_argument, &verbose_flag, 0},

    /* be compatible with old behavior */
    {"debug", no_argument, NULL, 'd'},
    {"daemon", no_argument, NULL, 'D'},
    {"config", required_argument, NULL, 'c'},
    {"log", required_argument, NULL, 'l'},
    {GETOPT_HELP_OPTION_DECL},
    {GETOPT_VERSION_OPTION_DECL},

    /* new options */
    {"nodebug", no_argument, &debug_flag, 0},
    {"nodaemon", no_argument, &daemon_flag, 0},

    {NULL, 0, NULL, 0}
};

/*
** return --
** 0: normal
** 1: usage 
** 2: version
** negative number: error
*/
static int __parse_opt(int argc, char *argv[], CLCConfig * c)
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
                return CLC_CONFIG_RET_ERR_NOMEM;
            break;

        case 'l':
            c->log_path = strdup(optarg);
            if (c->log_path == NULL)
                return CLC_CONFIG_RET_ERR_NOMEM;
            break;

        case 'h':
            ret = CLC_CONFIG_RET_HELP;
            break;

        case 'd':
            c->debug = 1;
            debug_flag = 1;
            break;

        case 'D':
            c->daemon = 1;
            daemon_flag = 1;
            break;

        case 'V':
            ret = CLC_CONFIG_RET_VER;
            break;

        default:
            ret = -1;
            break;
        }
    }
    c->verbose = verbose_flag;
    if (c->debug == UNDEFINED_CFG_INT && debug_flag != UNDEFINED_CFG_INT)
        /* in favor of short option */
        c->debug = debug_flag;
    if (c->daemon == UNDEFINED_CFG_INT && daemon_flag != UNDEFINED_CFG_INT)
        /* in favor of short option */
        c->daemon = daemon_flag;

    if (optind < argc) {
        logsimple("%s: non-option ARGV-elements: ", argv[0]);
        while (optind < argc)
            logsimple("%s ", argv[optind++]);
        logsimple("\n");
        ret = CLC_CONFIG_RET_ERR_CMD;
    }

    return ret;
}


/* use ini lib from ding-lib */

#include <path_utils.h>
#include <collection_tools.h>
#include <ini_config.h>

/* *v == NULL require space to be allocated */
static int __parse_oneitem_str(const char *k, char **v, int vlen,
                               struct collection_item *ini)
{
    struct collection_item *item;
    int error;

    if (get_config_item(NULL, k, ini, &item)) {
        logsimple(_("error reading value for %s\n"), k);
        return CLC_CONFIG_RET_ERR_CONF;
    }
    else {
        if (!item)
            return 0;

        const char *s = get_const_string_config_value(item, &error);
        if (error) {
            logsimple(_("error getting %s\n"), k);
            return CLC_CONFIG_RET_ERR_CONF;
        }
        else if (debug_flag == 1)
            logdebug(_("%s has value %s\n"), k, s);

        if (s == NULL || strlen(s) == 0)
            *v = NULL;
        else if (*v == NULL) {
            *v = strdup(s);
            if (*v == NULL)
                return CLC_CONFIG_RET_ERR_NOMEM;
        }
        else
            strncpy(*v, s, vlen);
    }

    return 0;
}

static int __parse_oneitem_int(const char *k, int *v,
                               struct collection_item *ini)
{
    struct collection_item *item;
    int error;

    if (get_config_item(NULL, k, ini, &item)) {
        logsimple(_("error reading value for %s\n"), k);
        return CLC_CONFIG_RET_ERR_CONF;
    }
    else {
        if (!item)
            return 0;

        *v = get_int_config_value(item, 1, 10, &error);
        if (error) {
            logsimple(_("error getting %s\n"), k);
            return CLC_CONFIG_RET_ERR_CONF;
        }
        else if (debug_flag == 1)
            logdebug(_("%s has value %d\n"), k, *v);
    }

    return 0;
}

static int __parse_config(CLCConfig * c)
{
    if (c == NULL)
        return CLC_CONFIG_RET_ERR_UNKNOWN;

    if (file_not_exist(c->conf_path))
        return CLC_CONFIG_RET_ERR_NOCONF;

    struct collection_item *ini_config = NULL;
    struct collection_item *error_set = NULL;

    if (config_from_file(PROGRAM_NAME, c->conf_path,
                         &ini_config, INI_STOP_ON_ANY, &error_set)) {
        logsimple(_("error while reading %s\n"), c->conf_path);
        return CLC_CONFIG_RET_ERR_CONF;
    }

    if (__parse_oneitem_str("LYCLC_MCAST_IP", &c->clc_mcast_ip,
                            0, ini_config) ||
        __parse_oneitem_int("LYCLC_MCAST_PORT", &c->clc_mcast_port,
                            ini_config) ||
        __parse_oneitem_str("LYCLC_IP", &c->clc_ip,
                            0, ini_config) ||
        __parse_oneitem_int("LYCLC_PORT", &c->clc_port,
                            ini_config) ||
        __parse_oneitem_str("LYCLC_DATA_DIR", &c->clc_data_dir,
                            0, ini_config) ||
        __parse_oneitem_str("LYCLC_PID_PATH", &c->pid_path,
                            0, ini_config) ||
        __parse_oneitem_str("LYCLC_DB_NAME", &c->db_name,
                            0, ini_config) ||
        __parse_oneitem_str("LYCLC_DB_USERNAME", &c->db_user,
                            0, ini_config) ||
        __parse_oneitem_str("LYCLC_DB_PASSWORD", &c->db_pass,
                            0, ini_config))
        return CLC_CONFIG_RET_ERR_CONF;

    if (c->daemon == UNDEFINED_CFG_INT) {
        if (__parse_oneitem_int("LYCLC_DAEMON", &c->daemon, ini_config))
            return CLC_CONFIG_RET_ERR_CONF;
    }
    if (c->debug == UNDEFINED_CFG_INT) {
        if (__parse_oneitem_int("LYCLC_DEBUG", &c->debug, ini_config))
            return CLC_CONFIG_RET_ERR_CONF;
    }
    if (c->log_path == NULL) {
        if (__parse_oneitem_str
            ("LYCLC_LOG_PATH", &c->log_path, 0, ini_config))
            return CLC_CONFIG_RET_ERR_CONF;
    }

    if (ini_config)
        free_ini_config(ini_config);

    if (error_set)
        free_ini_config_errors(error_set);

    return 0;
}

#include <arpa/inet.h>
static int __is_IP_valid(char *ip, int mcast)
{
    struct sockaddr_in sa;
    int ret = inet_pton(AF_INET, ip, &(sa.sin_addr));
    if (ret <= 0)
        return 0;
    else
        ret = 1;
    if (mcast)
        ret =
            (ntohl(sa.sin_addr.s_addr) & 0xf0000000) == 0xe0000000 ? 1 : 0;
    return ret;
}

static int __is_port_valid(int port)
{
    if (port <= 1024 || port > 65535)
        return 0;
    return 1;
}

void usage(void)
{

    printf(_("\
%s is the cloud controller of LuoYun Cloud Platform.\n\n\
"), PROGRAM_NAME);

    printf(_("\
Usage : %s [OPTION]\n\n\
"), PROGRAM_NAME);

    printf(_("  -c, --config    Specify the config file\n"
             "                  default is " DEFAULT_LYCLC_CONF_PATH " \n"
             "  -l, --log       log file, must be full path\n"
             "                  default is " DEFAULT_LYCLC_LOG_PATH " \n"
             "  -D, --daemon    run as a daemon\n"
             "  -d, --debug     debug mode\n"
             "  --verbose       verbose mode\n"
             "  --brief         suppress log message\n"
             "  --nodebug       suppress debug message\n"
             "  --nodaemon      not run as daemon\n"));
}

int clc_config(int argc, char *argv[], CLCConfig * c)
{
    int ret;

    if (c == NULL)
        return CLC_CONFIG_RET_ERR_UNKNOWN;      /* internal error */

    /* initialize CLCConfig with undefined values */
    bzero(c, sizeof(CLCConfig));
    c->verbose = UNDEFINED_CFG_INT;
    c->daemon = UNDEFINED_CFG_INT;
    c->debug = UNDEFINED_CFG_INT;
    c->conf_path = NULL;
    c->log_path = NULL;
    c->pid_path = NULL;
    c->db_name = NULL;
    c->db_user = NULL;
    c->db_pass = NULL;

    /* parse command line options */
    ret = __parse_opt(argc, argv, c);
    if (ret)
        return ret;             /* to exit program */

    /* check conf_path before reading it */
    if (c->conf_path == NULL) {
        c->conf_path = strdup(DEFAULT_LYCLC_CONF_PATH);
        if (c->conf_path == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }
    //else if (file_not_exist(c->conf_path))
    //    return CLC_CONFIG_RET_ERR_ERRCONF;

    /* parse config file */
    if (access(c->conf_path, R_OK) == 0) {
        ret = __parse_config(c);
        if (ret && ret != CLC_CONFIG_RET_ERR_NOCONF)
            return ret; /* to exit programe */
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
    if (c->clc_mcast_ip == NULL) {
        c->clc_mcast_ip = strdup(DEFAULT_LYCLC_MCAST_IP);
        if (c->clc_mcast_ip == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }
    if (c->clc_mcast_port == 0)
        c->clc_mcast_port = DEFAULT_LYCLC_MCAST_PORT;
    if (c->clc_data_dir == NULL) {
        c->clc_data_dir = strdup(DEFAULT_LYCLC_DATA_DIR);
        if (c->clc_data_dir == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }
    if (c->log_path == NULL) {
        c->log_path = strdup(DEFAULT_LYCLC_LOG_PATH);
        if (c->log_path == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }
    if (c->pid_path == NULL) {
        c->pid_path = strdup(DEFAULT_LYCLC_PID_PATH);
        if (c->pid_path == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }
    if (c->db_name == NULL) {
        c->db_name = strdup(DEFAULT_LYCLC_DB_NAME);
        if (c->db_name == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }
    if (c->db_user == NULL) {
        c->db_user = strdup(DEFAULT_LYCLC_DB_USER);
        if (c->db_user == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }
    if (c->db_pass == NULL) {
        c->db_pass = strdup(DEFAULT_LYCLC_DB_PASS);
        if (c->db_pass == NULL)
            return CLC_CONFIG_RET_ERR_NOMEM;
    }

    /* simple configuration validity checking */
    if (__is_IP_valid(c->clc_mcast_ip, 1) == 0) {
        logsimple(_("cloud controller mcast ip is invalid\n"));
        return CLC_CONFIG_RET_ERR_CONF;
    }
    if (__is_port_valid(c->clc_mcast_port) == 0) {
        logsimple(_("cloud controller port is invalid\n"));
        return CLC_CONFIG_RET_ERR_CONF;
    }
    if (__is_port_valid(c->clc_port) == 0) {
        logsimple(_("cloud controller port is invalid\n"));
        return CLC_CONFIG_RET_ERR_CONF;
    }
    if (c->clc_ip && __is_IP_valid(c->clc_ip, 0) == 0) {
        logsimple(_("cloud controller ip is invalid\n"));
        return CLC_CONFIG_RET_ERR_CONF;
    }
    if (c->log_path) {
        if (access(c->log_path, F_OK) && lyutil_create_file(c->log_path, 0) < 0) {
            logsimple(_("not able to create %s\n"), c->log_path);
            return CLC_CONFIG_RET_ERR_CMD;
        }
        if (access(c->log_path, W_OK)) {
            logsimple(_("not able to write to %s\n"), c->log_path);
            return CLC_CONFIG_RET_ERR_CMD;
        }
    }

    return ret;
}

