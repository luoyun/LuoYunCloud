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
#include <sys/epoll.h>
/* in RHEL5, EPOLLRDHUP is not defined */
#ifndef EPOLLRDHUP
#define EPOLLRDHUP 0x2000
#endif
#include <libpq-fe.h>

#include "../util/logging.h"
#include "../util/lypacket.h"
#include "../util/lyxml.h"
#include "../util/lyutil.h"
#include "options.h"
#include "entity.h"
#include "events.h"
#include "postgres.h"
#include "lyjob.h"
#include "lyclc.h"


#define LYCLC_PID_DIR "/var/run"

/* Global value */
CLCConfig *g_c = NULL;

static int __print_config(CLCConfig * c)
{
    logdebug("CLCConfig :\n"
             "  clc_ip = %s\n" "  clc_port = %d\n"
             "  clc_mcast_ip = %s\n" "  clc_mcast_port = %d\n"
             "  conf_path = %s\n"
             "  log_path = %s\n"
             "  DB info = %s,%s,%s\n"
             "  verbose = %d\n" "  debug = %d\n" "  daemon = %d\n",
             c->clc_ip, c->clc_port,
             c->clc_mcast_ip, c->clc_mcast_port,
             c->conf_path, c->log_path,
             c->db_name, c->db_user, c->db_pass,
             c->verbose, c->debug, c->daemon);

    return 0;
}

static void __main_clean(int keeppid)
{
    if (g_c == NULL)
        return;

    loginfo(_("%s exit normally\n"), PROGRAM_NAME);

    job_cleanup();
    ly_db_close();
    ly_clc_ip_clean();
    ly_entity_store_destroy();
    ly_epoll_close();
    if (keeppid == 0)
        lyutil_remove_pid_file(LYCLC_PID_DIR, PROGRAM_NAME);
    if (g_c->conf_path)
        free(g_c->conf_path);
    if (g_c->log_path)
        free(g_c->log_path);
    if (g_c->db_name)
        free(g_c->db_name);
    if (g_c->db_user)
        free(g_c->db_user);
    if (g_c->db_pass)
        free(g_c->db_pass);
    if (g_c->clc_ip)
        free(g_c->clc_ip);
    if (g_c->clc_mcast_ip)
        free(g_c->clc_mcast_ip);
    if (g_c->clc_data_dir)
        free(g_c->clc_data_dir);
    lyxml_cleanup();
    logclose();
    free(g_c);
    return;
}

static void __sig_handler(int sig, siginfo_t * si, void *unused)
{
    loginfo("%s was signaled to exit...\n", PROGRAM_NAME);
    __main_clean(0);
    exit(0);
}

int main(int argc, char *argv[])
{
    int ret, keeppidfile = 1;

    setlocale(LC_ALL, "");
    bindtextdomain(PACKAGE, LOCALEDIR);
    textdomain(PACKAGE);

    lyxml_init();
    lyauth_init();

    /* start initializeing g_c */
    CLCConfig *c = malloc(sizeof(CLCConfig));
    if (c == NULL) {
        printf(_("malloc for g_c have a error.\n"));
        return -255;
    }
    g_c = c;

    /* parse command line option and configuration file */
    ret = clc_config(argc, argv, c);
    if (ret == CLC_CONFIG_RET_HELP)
        usage();
    else if (ret == CLC_CONFIG_RET_VER)
        printf(_("%s : Version %s\n"), PROGRAM_NAME, PROGRAM_VERSION);
    else if (ret == CLC_CONFIG_RET_ERR_CMD)
        printf(_
               ("command line parsing error, use -h option to display usage\n"));
    else if (ret == CLC_CONFIG_RET_ERR_NOCONF) {
        printf(_
               ("missing lyclc config file, default build-in settings are used.\n"));
        ret = 0;
    }
    else if (ret == CLC_CONFIG_RET_ERR_ERRCONF)
        printf(_("can not find %s.\n"), c->conf_path);
    else if (ret == CLC_CONFIG_RET_ERR_CONF)
        printf(_("reading config file %s returned error\n"), c->conf_path);
    else if (ret == CLC_CONFIG_RET_ERR_UNKNOWN)
        printf(_("internal error\n"));

    /* exit if ret is not zero */
    if (ret != 0)
        goto out;

    /* for debuuging */
    if (c->debug)
        __print_config(c);

    /* make sure data directory exists */
    if (lyutil_create_dir(c->clc_data_dir)) {
        printf(_("%s is not accessible\n"), c->clc_data_dir);
        ret = -255;
        goto out;
    }

    /* get clc ip */
    if (c->clc_ip == NULL && ly_clc_ip_get() < 0) {
        logerror(_("CLC no proper network interface to use.\n"));
        goto out;
    }

    /* check whether program is started already */
    ret = lyutil_check_pid_file(LYCLC_PID_DIR, PROGRAM_NAME);
    if (ret == 1) {
        printf(_("%s is running already.\n"), PROGRAM_NAME);
        ret = 0;
        goto out;
    }
    else if (ret != 0) {
        printf(_("error checking pid file.\n"));
        goto out;
    }

    /* Daemonize the progress */
    if (c->daemon) {
        if (c->debug)
            lyutil_daemonize(c->log_path, LYDEBUG);
        else if (c->verbose)
            lyutil_daemonize(c->log_path, LYINFO);
        else
            lyutil_daemonize(c->log_path, LYWARN);
    }
    else
        logfile(NULL, c->debug ? LYDEBUG : c->verbose ? LYINFO : LYWARN);

    /* create lock file */
    ret = lyutil_create_pid_file(LYCLC_PID_DIR, PROGRAM_NAME);
    if (ret == 1) {
        logsimple(_("%s is running already.\n"), PROGRAM_NAME);
        ret = 0;
        goto out;
    }
    else if (ret != 0) {
        logsimple(_("error creating pid file.\n"));
        goto out;
    }
    keeppidfile = 0;

    /* set up signal handler */
    struct sigaction sa;
    sa.sa_flags = 0;
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = __sig_handler;
    if (sigaction(SIGTERM, &sa, NULL)) {
        logsimple(_("Setting signal handler error.\n"));
        ret = -255;
        goto out;
    }

    /* init db connection */
    if (ly_db_init() < 0) {
        logsimple(_("ly_entity_init failed.\n"));
        ret = -255;
        goto out;
    }

    /* initialize entity store */
    if (ly_entity_store_init() < 0) {
        logsimple(_("ly_entity_init failed.\n"));
        ret = -255;
        goto out;
    }

    /* init job queue */
    if (job_init() < 0 || job_internal_init() < 0) {
        logsimple(_("job_init failed.\n"));
        ret = -255;
        goto out;
    }
    if (c->debug)
        job_print_queue();

    /* initialize g_c->efd */
    if (ly_epoll_init(EPOLL_EVENTS_MAX) != 0) {
        logsimple(_("ly_epoll_init failed.\n"));
        ret = -255;
        goto out;
    }

    if (ly_epoll_work_start(g_c->clc_port) != 0) {
        ret = -1;
        logsimple(_("ly_epoll_init failed.\n"));
        goto out;
    }

    /* init timeout values */
    time_t mcast_join_time, job_dispatch_time, job_internal_time;
    mcast_join_time = 0;
    time(&job_dispatch_time);
    job_internal_time = job_dispatch_time + (CLC_MCAST_JOIN_INTERVAL<<1);
    job_dispatch_time = job_dispatch_time + (CLC_MCAST_JOIN_INTERVAL<<2);

    /* start main event driven loop */
    int i, n = 0;
    struct epoll_event events[EPOLL_EVENTS_MAX];
    while (1) {
        time_t time_now;
        time(&time_now);

        /* send mcast request */
        if (time_now - mcast_join_time > CLC_MCAST_JOIN_INTERVAL) {
            if (ly_mcast_send_join() < 0)
                logerror(_("failed sending mcast request.\n"));
            mcast_join_time = time_now;
        }
        else if (time_now < mcast_join_time)
            mcast_join_time = time_now;

        /* job dispatch */
        if (time_now - job_dispatch_time > CLC_JOB_DISPATCH_INTERVAL) {
            if (job_dispatch() < 0)
                logerror(_("job_dispatch failed.\n"));
            job_dispatch_time = time_now;
        }
        else if (time_now < job_dispatch_time)
            job_dispatch_time = time_now;

        /* internal job dispatch */
        if (time_now - job_internal_time > CLC_JOB_INTERNAL_INTERVAL) {
            if (job_internal_dispatch() < 0)
                logerror(_("job_internal failed.\n"));
            job_internal_time = time_now;
        }
        else if (time_now < job_internal_time)
            job_internal_time = time_now;

        n = epoll_wait(g_efd, events, EPOLL_EVENTS_MAX,
                       CLC_EPOLL_TIMEOUT);
        if (n != 0)
            logdebug(_("waiting ... got %d events\n"), n);
        for (i = 0; i < n; i++) {
            int id = events[i].data.fd;
            if (events[i].events & EPOLLIN) {
                ret = ly_epoll_entity_recv(id);
                if (ret < 0) {
                    logerror(_("epoll_data_recv error\n"));
                }
                else if (ret > 0) {
                    loginfo(_("release entity %d\n"), id);
                    ly_entity_release(id);
                }
            }
            else if (events[i].events & EPOLLRDHUP) {
                loginfo(_("epoll entity(%d) got rdhup. close.\n"), id);
                ly_entity_release(id);
            }
            else if (events[i].events & EPOLLHUP) {
                loginfo(_("epoll entity(%d) got hup. close.\n"), id);
                ly_entity_release(id);
            }
            else {
                logerror(_("unexpected event(%d, %d). ignore.\n"),
                         events[i].events, id);
            }
        }
    }

out:
    __main_clean(keeppidfile);
    return ret;
}
