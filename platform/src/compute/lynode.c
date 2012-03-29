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
#include <signal.h>
#include <time.h>

#include "../util/logging.h"
#include "../util/lypacket.h"
#include "../util/lyxml.h"
#include "../util/lyutil.h"
#include "options.h"
#include "events.h"
#include "domain.h"
#include "node.h"

/* Global value */
NodeControl *g_c = NULL;

static int __print_config(NodeConfig *c)
{
    logdebug("NodeControl :\n"
             "  clc_ip = %s\n" "  clc_port = %d\n"
             "  clc_mcast_ip = %s\n" "  clc_mcast_port = %d\n"
             "  auto_connect = %d\n"
             "  node_data_dir = %s\n"
             "  conf_path = %s\n"
             "  sysconf_path = %s\n"
             "  log_path = %s\n"
             "  verbose = %d\n" "  debug = %d\n" "  daemon = %d\n",
             c->clc_ip, c->clc_port,
             c->clc_mcast_ip, c->clc_mcast_port,
             c->auto_connect,
             c->node_data_dir, c->conf_path, c->sysconf_path, c->log_path,
             c->verbose, c->debug, c->daemon);

    return 0;
}

static void __main_clean(int keeppid)
{
    if (g_c == NULL)
        return;


    NodeConfig *c = &g_c->config;
    NodeSysConfig *s = &g_c->config_sys;

    ly_epoll_close();
    libvirt_close();
    if (keeppid == 0)
        lyutil_remove_pid_file(c->node_data_dir, PROGRAM_NAME);
    lyauth_free(&g_c->auth);
    if (c->clc_ip)
        free(c->clc_ip);
    if (c->clc_mcast_ip)
        free(c->clc_mcast_ip);
    if (c->conf_path)
        free(c->conf_path);
    if (c->sysconf_path)
        free(c->sysconf_path);
    if (c->node_data_dir)
        free(c->node_data_dir);
    if (c->log_path)
        free(c->log_path);
    if (s->clc_ip)
        free(s->clc_ip);
    if (s->node_secret)
        free(s->node_secret);
    if (g_c->clc_ip)
        free(g_c->clc_ip);
    if (g_c->node_ip)
        free(g_c->node_ip);
    if (g_c->node) {
        luoyun_node_info_cleanup(g_c->node);
        free(g_c->node);
    }
    free(g_c);
    logclose();
    lyxml_cleanup();
    return;
}

/* update sysconf file */
int ly_sysconf_save(void)
{
    NodeConfig *c = &g_c->config;
    NodeSysConfig *s = &g_c->config_sys;
    AuthConfig *ac = &g_c->auth;
    NodeInfo *nf = g_c->node;

    int updated = 0;
    if (g_c->clc_ip) {
        if (s->clc_ip == NULL || strcmp(s->clc_ip, g_c->clc_ip) != 0) {
            updated = 1;
            if (s->clc_ip)
                free(s->clc_ip);
            s->clc_ip = strdup(g_c->clc_ip);
        }
    }
    if (s->clc_port != g_c->clc_port) {
        updated = 1;
        s->clc_port = g_c->clc_port;
    }
    if (nf && s->node_tag != nf->host_tag) {
        updated = 1;
        s->node_tag = nf->host_tag;
    }
    if (ac->secret) {
        if (s->node_secret == NULL ||
            strcmp(s->node_secret, ac->secret) != 0) {
            updated = 1;
            if (s->node_secret)
                free(s->node_secret);
            s->node_secret = strdup(ac->secret);
        }
    }
    if (!updated)
        return 0;

    time_t tnow = time(NULL);
   
    FILE *fp = fopen(c->sysconf_path, "w");
    if (fp == NULL)
        return -1;

    fprintf(fp, "# Automatically updated\n"
                "# last update was on %s\n"  
                "LYCLC_HOST = %s\nLYCLC_PORT = %d\n"
                "LYNODE_TAG = %d\nLYNODE_SECRET = %s\n",
                 ctime(&tnow),
                 s->clc_ip, s->clc_port,
                 s->node_tag, s->node_secret);
    fclose(fp);
    return 0;
}

static void __sig_handler(int sig, siginfo_t *si, void *unused)
{
    loginfo("%s was signaled to exit...\n", PROGRAM_NAME);
    __main_clean(0);
    exit(0);
}

int main(int argc, char *argv[])
{
    int ret, keeppidfile=1;

    setlocale(LC_ALL, "");
    bindtextdomain(PACKAGE, LOCALEDIR);
    textdomain(PACKAGE);

    lyxml_init();
    lyauth_init();

    /* start initializeing g_c */
    g_c = malloc(sizeof(NodeControl));
    if (g_c == NULL) {
        printf(_("malloc for g_c have a error.\n"));
        return -255;
    }
    bzero(g_c, sizeof(NodeControl));
    g_c->node = NULL;
    g_c->mfd_cmsg = NULL;
    g_c->efd = -1;
    g_c->mfd = -1;
    g_c->wfd = -1;
    NodeConfig *c = &g_c->config;
    NodeSysConfig *s = &g_c->config_sys;

    /* parse command line option and configuration file */
    ret = node_config(argc, argv, c, s);
    if (ret == NODE_CONFIG_RET_HELP)
        usage();
    else if (ret == NODE_CONFIG_RET_VER)
        printf(_("%s : Version %s\n"), PROGRAM_NAME, PROGRAM_VERSION);
    else if (ret == NODE_CONFIG_RET_ERR_CMD)
        printf(_("command line parsing error, use -h option to display usage\n"));
    else if (ret == NODE_CONFIG_RET_ERR_NOCONF){
        printf(_("missing lynode config file, default build-in settings are used.\n"));
        ret = 0;
    }
    else if (ret == NODE_CONFIG_RET_ERR_ERRCONF)
        printf(_("can not find %s.\n"), c->conf_path);
    else if (ret == NODE_CONFIG_RET_ERR_CONF)
        printf(_("reading config file %s returned error\n"), c->conf_path);
    else if (ret == NODE_CONFIG_RET_ERR_UNKNOWN)
        printf(_("internal error\n"));

    /* exit if ret is not zero */
    if (ret != 0)
        goto out;

    /* identify the clc info to use */
    if (c->auto_connect == DISABLE) {
        g_c->clc_ip = strdup(c->clc_ip);
        g_c->clc_port = c->clc_port;
    }
    else if (s->clc_ip) {
        g_c->clc_ip = strdup(s->clc_ip);
        g_c->clc_port = s->clc_port;
    }

    /* init node state */
    if (g_c->clc_ip)
        g_c->state = NODE_STATUS_UNINITIALIZED;
    else
        g_c->state = NODE_STATUS_INITIALIZED;

    /* get secret */
    if (s->node_secret)
        g_c->auth.secret = strdup(s->node_secret);

    /* for debuuging */
    if (c->debug)
        __print_config(c);

    /* make sure data directory exists */
    if (lyutil_create_dir(c->node_data_dir)) {
        printf(_("%s is not accessible\n"), c->node_data_dir);
        ret = -255;
        goto out;
    }

    /* check whether program is started already */
    ret = lyutil_check_pid_file(c->node_data_dir, PROGRAM_NAME);
    if (ret == 1) {
        printf(_("%s is running already.\n"), PROGRAM_NAME);
        ret = 0;
        goto out;
    }
    else if (ret != 0) {
        printf(_("error checking pid file.\n"));
        goto out;
    }

    /* Connect to libvirt daemon */
    if (libvirt_check(c->driver) < 0) {
        logsimple(_("error connecting hypervisor.\n"));
        ret = -255;
        goto out;
    }

    /* Daemonize the progress */
    if (c->daemon) {
        if (c->debug == LYDEBUG)
            printf(_("Run as daemon, log to %s.\n"), c->log_path);
        lyutil_daemonize(__main_clean, keeppidfile);
        logfile(c->log_path, c->debug ? LYDEBUG : c->verbose ? LYINFO : LYWARN);
    }
    else
        logfile(NULL, c->debug ? LYDEBUG : c->verbose ? LYINFO : LYWARN);
    logcallback(ly_node_send_report, 0);

    /* create lock file */
    ret = lyutil_create_pid_file(c->node_data_dir, PROGRAM_NAME);
    if (ret == 1) {
        logsimple(_("%s is running already.\n"), PROGRAM_NAME);
        goto out;
    }
    else if (ret != 0) {
        logsimple(_("error creating pid file.\n"));
        goto out;
    }
    keeppidfile = 0;

    /* Connect to libvirt daemon */
    if (libvirt_connect(c->driver) < 0) {
        logsimple(_("error connecting hypervisor.\n"));
        ret = -255;
        goto out;
    }

    /* Init node info */
    g_c->node = ly_node_info_init();
    if (g_c->node == NULL) {
        logsimple(_("error initializing node info.\n"));
        ret = -255;
        goto out;
    }
    NodeInfo * nf = g_c->node;
    nf->host_tag = s->node_tag;
    if (c->debug)
        luoyun_node_info_print(nf);

    /* set up signal handler */
    lyutil_signal_init();

    /* handle specific signal */
    struct sigaction sa;
    sa.sa_flags = 0;
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = __sig_handler;
    if (sigaction(SIGTERM, &sa, NULL)) {
        logsimple(_("Setting signal handler error.\n"));
        ret = -255;
        goto out;
    }

    /* block SIGCHLD */
    sigset_t sig;
    sigemptyset(&sig);
    sigaddset(&sig, SIGCHLD);
    pthread_sigmask(SIG_BLOCK, &sig, NULL);

    /* initialize g_c->efd */
    if (ly_epoll_init(MAX_EVENTS) != 0) {
        logsimple(_("ly_epoll_init failed.\n"));
        ret = -255;
        goto out;
    }

    /* start main event driven loop */
    int i, n;
    int wait = -1;
    struct epoll_event events[MAX_EVENTS];
    while (1) {
        if (g_c->clc_ip == NULL) {
            /* start listening on clc mcast */
            if (g_c->mfd < 0 && ly_epoll_mcast_register() != 0) {
                logerror(_("listening on clc mcast error.\n"));
                ret = -1;
                break;
            }
            loginfo(_("wait for clc mcast join request...\n"));
        }
        else if (g_c->wfd < 0 && wait < 0) {
            /* init node state */
            if (nf->host_tag > 0)
                g_c->state = NODE_STATUS_INITIALIZED;
            else
                g_c->state = NODE_STATUS_UNINITIALIZED;
            /* start node registration */
            if ((ly_epoll_work_register() != 0 || ly_register_node() != 0)) {
                /* close work socket */
                ly_epoll_work_close();
                logerror(_("failed registering node. will try again\n"));

                if (c->auto_connect == ALWAYS) {
                    free(g_c->clc_ip);
                    g_c->clc_ip = NULL;
                    continue;
                }
                else {
                    wait = LY_NODE_EPOLL_WAIT;
                    loginfo(_("wait before retry...\n"));
                }
            }
        }

        logdebug(_("waiting for events ...\n"));
        n = epoll_wait(g_c->efd, events, MAX_EVENTS, wait);
        if (wait > 0)
            wait = -1;
        loginfo(_("waiting ... got %d events\n"), n);
        for (i = 0; i < n; i++) {
            if (LY_EVENT_MCAST_DATAIN(events[i])) {
                /* mcast data received */
                ret = ly_epoll_mcast_recv();
                if (ret < 0) {
                    logwarn(_("unexpected clc mcast data recevied.\n"));
                }
                else if (ret == 0) {
                    logdebug(_("ly_epoll_mcast_recv returns 0. do nothing.\n"));
                }
                else {
                    /* the clc ip/port are obtained from mcast */
                    loginfo(_("new clc mcast data received. "
                              "re-registering....\n"));
                    ly_epoll_mcast_close();
                }
            }
            else if (LY_EVENT_WORK_DATAIN(events[i])) {
                /* clc data received */
                ret = ly_epoll_work_recv();
                if (ret == 0) {
                    logdebug(_("ly_epoll_work_recv return 0. continue reading...\n"));
                    continue;
                }

                /* in all other cases, close work socket */
                ly_epoll_work_close();
                if (ret < 0)
                    logwarn(_("unexpected work process error. "
                              "will reopen work socket ...\n"));
                else
                    logwarn(_("node work socket closed. "
                              "will reopen ...\n"));
                if (c->auto_connect == ALWAYS) {
                    free(g_c->clc_ip);
                    g_c->clc_ip = NULL;
                 }
            }
            else if (events[i].events & EPOLLRDHUP) {
                /* work closed by clc */
                logdebug(_("close by remote\n"));
                ly_epoll_work_close();
            }
            else {
                logwarn(_("unexpected epoll event(%d) for %d\n"),
                           events[i].events, events[i].data.fd);
            }
        }
    }

out:
    __main_clean(keeppidfile);
    if (ret <= 0)
        loginfo(_("%s exits\n"), PROGRAM_NAME);
    return ret;
}
