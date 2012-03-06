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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <unistd.h>
#include <getopt.h>

#include "lyosm.h"
#include "osmmisc.h"
#include "osmutil.h"
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
    {"key", required_argument, NULL, 'k'},
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
static int __parse_opt(int argc, char *argv[], OSMConfig * c)
{
    int ret = 0, opt = 0;
    const char *const short_options = "c:hdDk:l:V";

    while (1) {
        /* getopt_long stores the option index here */
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
                return OSM_CONFIG_RET_ERR_NOMEM;
            break;

        case 'l':
            c->log_path = strdup(optarg);
            if (c->log_path == NULL)
                return OSM_CONFIG_RET_ERR_NOMEM;
            break;

        case 'k':
            c->key_path = strdup(optarg);
            if (c->key_path == NULL)
                return OSM_CONFIG_RET_ERR_NOMEM;
            break;

        case 'h':
            ret = OSM_CONFIG_RET_HELP;
            break;

        case 'd':
            c->debug = 1;
            break;

        case 'D':
            c->daemon = 1;
            break;

        case 'V':
            ret = OSM_CONFIG_RET_VER;
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
        ret = OSM_CONFIG_RET_ERR_CMD;
    }

    return ret;
}

static int __parse_config (OSMConfig *c)
{
    FILE *fp;
    char line[LINE_MAX];
    char *kstr; /* point to the key string */
    char *vstr; /* point to the value string */

    if (access(c->conf_path, F_OK) != 0)
        return OSM_CONFIG_RET_ERR_NOCONF;

    fp = fopen(c->conf_path, "r");
    if (fp == NULL )
        return OSM_CONFIG_RET_ERR_ERRCONF;

    while ( 1 ) {
        if (fgets(line, LINE_MAX, fp) == NULL )
            break;

        if (str_filter_white_space(line) != 0)
            continue;

        if (line[0] == '#')
            continue;

        vstr = strstr(line, "=");
        if (vstr == NULL )
            continue;
        else
            vstr++;

        if ((kstr = strstr(line, "CLC_IP")) != NULL)
            c->clc_ip = strdup(vstr);
        else if ((kstr = strstr(line, "CLC_PORT")) != NULL)
            c->clc_port = atoi(vstr);
        else if ((kstr = strstr(line, "CLC_MCAST_IP")) != NULL)
            c->clc_mcast_ip = strdup(vstr);
        else if ((kstr = strstr(line, "CLC_MCAST_PORT")) != NULL)
            c->clc_mcast_port = atoi(vstr);
        else if ((kstr = strstr(line, "TAG")) != NULL)
            c->osm_tag = atoi(vstr);
        else
            logsimple("Not support configuration: %s\n", line);
    }

    fclose(fp);
    return 0;
}

int __read_secret(OSMConfig *c)
{
    FILE *fp;
    char line[LINE_MAX];
    fp = fopen(c->key_path, "r");
    if (fp == NULL )
        return OSM_CONFIG_RET_ERR_ERRCONF;
    if (fgets(line, LINE_MAX, fp) == NULL) {
        fclose(fp);
        return OSM_CONFIG_RET_ERR_ERRCONF;
    }
    fclose(fp);

    int len = strlen(line);
    if (len <= 0 || len >= LINE_MAX-1)
        return OSM_CONFIG_RET_ERR_ERRCONF;

    if (line[len-1] == '\n')
        line[len-1] = '\0';
    c->osm_secret = strdup(line);
    return 0;
}

int osm_config(int argc, char *argv[], OSMConfig *c)
{
    int ret;

    if (c == NULL)
        return OSM_CONFIG_RET_ERR_UNKNOWN; /* internal error */

    /* initialize NodeConfig with undefined values */
    bzero(c, sizeof(OSMConfig));

    /* parse command line options */
    ret = __parse_opt(argc, argv, c);
    if (ret)
        return ret; /* to exit program */

    /* init conf_path */
    if (c->conf_path == NULL) {
        c->conf_path = strdup(DEFAULT_OSM_CONF_PATH);
        if (c->conf_path == NULL)
            return OSM_CONFIG_RET_ERR_NOMEM;
    }

    /* init key_path */
    if (c->key_path == NULL) {
        c->key_path = strdup(DEFAULT_OSM_KEY_PATH);
        if (c->key_path == NULL)
            return OSM_CONFIG_RET_ERR_NOMEM;
    }

    /* init conf_path */
    if (c->log_path == NULL) {
        c->log_path = strdup(DEFAULT_OSM_LOG_PATH);
        if (c->log_path == NULL)
            return OSM_CONFIG_RET_ERR_NOMEM;
        char * d = strdup(c->log_path);
        char * d_slash = rindex(d, '/');
        if (d_slash == NULL ) {
            if (d)
                free(d);
            return OSM_CONFIG_RET_ERR_UNKNOWN;
        }
        *d_slash = '\0';
        if (lyutil_create_dir(d) != 0) {
            free(d);
            logsimple("failed creating directory %s\n", d);
            return OSM_CONFIG_RET_ERR_UNKNOWN;
        }
        free(d);
        if (touch(c->log_path) != 0) {
            logsimple("not able to create %s\n", c->log_path);
            return OSM_CONFIG_RET_ERR_UNKNOWN;
        }
    }

    /* parse config file */
    ret = __parse_config(c);
    if (c->clc_ip == NULL)
        ret = OSM_CONFIG_RET_ERR_CONF;

    /* read secret key file */
    ret = __read_secret(c);
    if (c->osm_secret == NULL)
        ret = OSM_CONFIG_RET_ERR_CONF;

    return ret;
}

void usage(void)
{
    printf("\
%s is the OS manager of LuoYun Cloud Platform.\n\n\
", PROGRAM_NAME);

    printf("\
Usage : %s [OPTION]\n\n\
", PROGRAM_NAME);

    printf(  "  -c, --config    Specify the config file\n"
             "                  default is " DEFAULT_OSM_CONF_PATH " \n"
             "  -k, --key       key file, must be full path\n"
             "                  default is " DEFAULT_OSM_KEY_PATH " \n"
             "  -l, --log       log file, must be full path\n"
             "                  default is " DEFAULT_OSM_LOG_PATH " \n"
             "  -D, --daemon    run as a daemon\n"
             "  -d, --debug     debug mode\n"
             "  -v, --verbose   verbose mode\n");
}
