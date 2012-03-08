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
#include <signal.h>
#include <time.h>

#include "../luoyun/luoyun.h"
#include "lyosm.h"
#include "osmanager.h"
#include "options.h"
#include "events.h"
#include "osmutil.h"

OSMControl * g_c = NULL;
int g_app_status = -1;

static int __print_config(OSMConfig *c)
{
    printf("OSMControl :\n"
             "  clc_ip = %s\n" "  clc_port = %d\n"
             "  clc_mcast_ip = %s\n" "  clc_mcast_port = %d\n"
             "  conf_path = %s\n"
             "  log_path = %s\n"
             "  verbose = %d\n" "  debug = %d\n" "  daemon = %d\n",
             c->clc_ip, c->clc_port,
             c->clc_mcast_ip, c->clc_mcast_port,
             c->conf_path, c->log_path,
             c->verbose, c->debug, c->daemon);

    return 0;
}

static void __main_clean(int keeppid)
{
    OSMConfig *c = &g_c->config;

    loginfo("%s exit normally\n", PROGRAM_NAME);
    ly_epoll_close();
    lyauth_free(&g_c->auth);
    LY_SAFE_FREE(c->clc_ip)
    LY_SAFE_FREE(c->clc_mcast_ip)
    LY_SAFE_FREE(c->osm_secret)
    LY_SAFE_FREE(c->log_path)
    LY_SAFE_FREE(c->conf_path)
    LY_SAFE_FREE(c->storage_ip)
    LY_SAFE_FREE(c->storage_parm)
    LY_SAFE_FREE(g_c->clc_ip)
    LY_SAFE_FREE(g_c->osm_ip)
    free(g_c);
    logclose();
    return;
}

static void __sig_handler(int sig, siginfo_t *si, void *unused)
{
    loginfo("%s was signaled to exit...\n", PROGRAM_NAME);
    __main_clean(0);
    exit(0);
}

#include <pthread.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <limits.h>
void * __app_status_func(void * arg)
{
    char cmd[PATH_MAX];
    snprintf(cmd, PATH_MAX, "%s/status", g_c->config.scripts_dir);
    while(1) {

        sleep(LY_OSM_STATUS_CHECK_INTVL);

        if (g_c->wfd < 0) {
            loginfo("work socket is not ready %s\n", cmd);
            continue;
        }

        if (access(cmd, X_OK)) {
            logerror("can not execute %s\n", cmd);
            continue;
        }

        pid_t pid = vfork();
        if (pid < 0) {
            logerror("fork failed\n");
            continue;
        }

        if (pid) {
            int status;
            waitpid(pid, &status, 0);
            if (WIFEXITED(status)) {
                status = WEXITSTATUS(status);
                if (status == 0 && g_app_status != 0) {
                    loginfo("checking applicaiton status: "
                            "application is running\n");
                    ly_osm_report(LY_S_APP_RUNNING);
                }
                else if (status != 0) {
                    loginfo("checking applicaiton status: "
                            "application returns %d\n", status);
                    ly_osm_report(LY_S_APP_RUNNING+status);
                }
                g_app_status = status;
            }
            else {
                ly_osm_report(LY_S_APP_UNKNOWN);
                g_app_status = -1;
            }
            continue;
        }

        /* child process */
        char *argv[] = {"status", g_c->config.conf_path, NULL};
        execv(cmd, argv);
        logerror("excv failed\n");
        exit(127);
    }
}

int main(int argc, char *argv[])
{
    int ret, keeppidfile=1;

    lyauth_init();

    /* start initializeing g_c */
    g_c = malloc(sizeof(OSMControl));
    if (g_c == NULL) {
        printf("malloc for g_c have a error.\n");
        return -255;
    }
    bzero(g_c, sizeof(OSMControl));
    g_c->mfd_cmsg = NULL;
    g_c->efd = -1;
    g_c->mfd = -1;
    g_c->wfd = -1;
    OSMConfig *c = &g_c->config;

    /* parse command line option and configuration file */
    ret = osm_config(argc, argv, c);
    if (ret == OSM_CONFIG_RET_HELP)
        usage();
    else if (ret == OSM_CONFIG_RET_VER)
        printf("%s : Version %s\n", PROGRAM_NAME, PROGRAM_VERSION);
    else if (ret == OSM_CONFIG_RET_ERR_CMD)
        printf("command line parsing error, use -h option to display usage\n");
    else if (ret == OSM_CONFIG_RET_ERR_NOCONF)
        printf("missing osmanager config file\n");
    else if (ret == OSM_CONFIG_RET_ERR_ERRCONF)
        printf("can not find %s.\n", c->conf_path);
    else if (ret == OSM_CONFIG_RET_ERR_CONF)
        printf("reading config file %s returned error\n", c->conf_path);
    else if (ret == OSM_CONFIG_RET_ERR_UNKNOWN)
        printf("internal error\n");

    /* exit if ret is not zero */
    if (ret != 0)
        goto out;

    /* init g_c */
    g_c->clc_ip = strdup(c->clc_ip);
    g_c->clc_port = c->clc_port;
    if (c->osm_secret)
        g_c->auth.secret = strdup(c->osm_secret);
    g_c->state = OSM_STATUS_INIT;

    /* print out */
    if (c->debug || c->verbose)
        __print_config(c);

    /* Daemonize the progress */
    if (c->daemon) {
        if (c->debug || c->verbose)
            printf("Run as daemon, log to %s.\n", c->log_path);
        lyutil_daemonize();
        logfile(c->log_path, c->debug ?
                             LYDEBUG : c->verbose ? LYINFO : LYWARN);
    }
    else
        logfile(NULL, c->debug ? LYDEBUG : c->verbose ? LYINFO : LYWARN);

    /* set up signal handler */
    struct sigaction sa;
    sa.sa_flags = 0;
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = __sig_handler;
    if (sigaction(SIGTERM, &sa, NULL)) {
        logsimple("Setting signal handler error.\n");
        ret = -255;
        goto out;
    }

    /* start app status monitor thread */
    pthread_t __app_status_tid;
    if (pthread_create(&__app_status_tid, NULL,
                       __app_status_func, NULL) != 0) {
        logerror("threading __app_status_func, failed\n");
        goto out;
    }

    /* initialize g_c->efd */
    if (ly_epoll_init(MAX_EVENTS) != 0) {
        logsimple("ly_epoll_init failed.\n");
        ret = -255;
        goto out;
    }

    /* start main event driven loop */
    int i, n;
    int wait = -1;
    struct epoll_event events[MAX_EVENTS];
    while (1) {
        if (g_c->wfd < 0 && wait < 0) {
            /* init osm state */
            g_c->state = OSM_STATUS_INIT;
            /* start osm registration */
            if (ly_epoll_work_register() != 0) {
                /* failed connecting clc */
                LY_SAFE_FREE(g_c->clc_ip)
                loginfo("wait for mcast join...\n");
                if (g_c->mfd < 0 && ly_epoll_mcast_register() != 0) {
                    logerror("listening on clc mcast error. will try again\n");
                    wait = LY_OSM_EPOLL_WAIT;
                }
            }
            else if (ly_osm_register() != 0) {
                /* unexpected error. close work socket */
                ly_epoll_work_close();
                wait = LY_OSM_EPOLL_WAIT;
                logerror("failed registering osm. will try again\n");
            }
        }

        logdebug("waiting...\n");
        n = epoll_wait(g_c->efd, events, MAX_EVENTS, wait);
        if (wait > 0)
            wait = -1;
        loginfo("waiting ... got %d events\n", n);
        for (i = 0; i < n; i++) {
            if (LY_EVENT_MCAST_DATAIN(events[i])) {
                /* mcast data received */
                ret = ly_epoll_mcast_recv();
                if (ret < 0) {
                    logwarn("unexpected clc mcast data recevied.\n");
                    ly_epoll_mcast_close();
                    wait = -1;
                }
                else if (ret == 0) {
                    logdebug("ly_epoll_mcast_recv returns 0. do nothing.\n");
                }
                else {
                    /* the clc ip/port are obtained from mcast */
                    loginfo("new clc mcast data received. "
                            "re-registering....\n");
                    ly_epoll_mcast_close();
                    wait = -1;
                }
            }
            else if (LY_EVENT_WORK_DATAIN(events[i])) {
                /* clc data received */
                ret = ly_epoll_work_recv();
                if (ret == 0) {
                    logdebug("ly_epoll_work_recv return 0. continue...\n");
                    continue;
                }

                /* in all other cases, close work socket */
                ly_epoll_work_close();
                if (ret < 0)
                    logwarn("unexpected work process error\n");
                else
                    logwarn("osm socket closed. will try again... \n");
                wait = LY_OSM_EPOLL_WAIT;
            }
            else if (events[i].events & EPOLLRDHUP) {
                /* work closed by clc */
                logdebug("close by remote\n");
                ly_epoll_work_close();
            }
            else {
                logwarn("unexpected epoll event(%d) for %d\n",
                         events[i].events, events[i].data.fd);
            }
        }
    }

    logerror("should never see this message\n");
out:
    __main_clean(keeppidfile);
    return ret;
}
