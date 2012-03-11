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
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <unistd.h>             /* gethostname */
#include <netdb.h>              /* struct hostent */
#include <time.h>
#include <errno.h>
#include <sys/epoll.h>
/* in RHEL5, EPOLLRDHUP is not defined */
#ifndef EPOLLRDHUP
#define EPOLLRDHUP 0x2000
#endif

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "../util/lypacket.h"
#include "../util/lyxml.h"
#include "../util/lyutil.h"
#include "lyclc.h"
#include "entity.h"
#include "lyjob.h"
#include "events.h"
#include "postgres.h"


int g_efd = -1;

/* for debugging, print recv buf */
static void __print_recv_buf(char *buf, int size)
{
    int i;
    for (i=0; i<8; i++)
        logsimple("%02x ", buf[i]);
    logsimple("\n");
    LYPacketHeader h = *(LYPacketHeader *)buf;
    int type = h.type;
    int len = h.length;
    logsimple("type = %d, length = %d\n", type, len);

    return;
}


/* clc work socket receives connection */
static int __epoll_work_recv(int ent_id)
{
    int fd = ly_entity_fd(ent_id);
    if (fd == -1)
        return -255;

    struct sockaddr in_addr;
    socklen_t in_len;
    int infd;

    in_len = sizeof(in_addr);
    infd = accept(fd, &in_addr, &in_len);
    if (infd == -1) {
        if ((errno == EAGAIN) || (errno == EWOULDBLOCK)) {
            /* We have processed all incoming connections. */
            logdebug(_("accept error(%d) ignored\n"), errno);
            return 0;
        }
        else {
            logerror(_("unexpected accept error(%d) in %s"), errno,
                     __func__);
            return -1;
        }
    }

    char hbuf[NI_MAXHOST], sbuf[NI_MAXSERV];
    int ret = getnameinfo(&in_addr, in_len, hbuf, sizeof(hbuf),
                          sbuf, sizeof(sbuf),
                          NI_NUMERICHOST | NI_NUMERICSERV);
    if (ret)
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
    else
        loginfo(_("accepted connection from %s:%s. open socket %d\n"),
                  hbuf, sbuf, infd);

    /* keep alive */
    if (lyutil_set_keepalive(infd, CLC_SOCKET_KEEPALIVE_INTVL,
                                   CLC_SOCKET_KEEPALIVE_INTVL,
                                   CLC_SOCKET_KEEPALIVE_PROBES) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        close(infd);
        return -1;
    }

    int id = ly_entity_new(infd);
    if (id < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        close(infd);
        return -1;
    }
    struct epoll_event ev;
    ev.data.fd = id;
    ev.events = EPOLLIN;
    ret = epoll_ctl(g_efd, EPOLL_CTL_ADD, infd, &ev);
    if (ret == -1) {
        logerror(_("add socket to epoll error in %s.\n"), __func__);
        ly_entity_release(id);
        /* close(infd); closed in ly_entity_release */
        return -1;
    }
    loginfo(_("entity %d registered in epoll.\n"), id);

    return 0;
}

/* process new job request from web */
static int __process_web_job(char * buf, int size, int ent_id)
{
    logdebug(_("%s called\n"), __func__);

    if (size != sizeof(int32_t)) {
        logerror(_("unexpected web job data size\n"));
        return -1;
    }

    int job_id = *(int32_t *)buf;
    logdebug(_("web job id %d\n"), job_id);

    LYJobInfo *job = malloc(sizeof(LYJobInfo));
    if (job == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    job->j_id = job_id;
    if (db_job_get(job) != 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        free(job);
        return -1;
    }

    if (job_exist(job)){
        logwarn(_("job %d exists already\n"), job_id);
        free(job);
        return 0;
    }

    int ret = job_check(job);
    if (ret){
        logwarn(_("job check for job %d returns %d\n"), job_id, ret);
        if (!JOB_IS_CANCELLED(ret))
            ret = LY_S_CANCEL_INTERNAL_ERROR;
        /* can not use job_remove */
        time(&job->j_started);
        time(&job->j_ended);
        job->j_status = ret;
        db_job_update_status(job);
        free(job);
        return 0;
    }

    if (job_insert(job) != 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        time(&job->j_started);
        time(&job->j_ended);
        job->j_status = LY_S_CANCEL_INTERNAL_ERROR;
        db_job_update_status(job);
        free(job);
        return -1;
    }

    return 0;
}

/* process echo request */
static int __process_test_echo(char * buf, int size, int ent_id)
{
    logdebug(_("sending echo reply ...\n"));
    logdebug(_("%s\n"), buf);
    int fd = ly_entity_fd(ent_id);
    return ly_packet_send(fd, PKT_TYPE_TEST_ECHO_REPLY, buf, size);
}

int ly_epoll_entity_recv(int ent_id)
{
    if (ly_entity_type(ent_id) == LY_ENTITY_CLC)
        return __epoll_work_recv(ent_id);

    int fd = ly_entity_fd(ent_id);
    LYPacketRecv *pkt = ly_entity_pkt(ent_id);
    if (pkt == NULL)
        return -255;

    int size;
    void * buf = ly_packet_buf(pkt, &size);
    if (buf == NULL) {
        logerror(_("ly_packet_buf returns NULL buffer. close socket\n"));
        return 1;
    }
    if (size == 0) {
        logerror(_("ly_packet_buf returns 0 size buffer. close socket\n"));
        return 1;
    }

    int len = recv(fd, buf, size, 0);
    if (len < 0) {
        loginfo(_("socket %d recv returns %d, errno %d. close socket\n"),
                   fd, len, errno);

        if (ly_entity_type(ent_id) != LY_ENTITY_OSM)
            return 1;

        int db_id = ly_entity_db_id(ent_id);
        logdebug(_("update instance %d status in db\n"), db_id);
        InstanceInfo ii;
        ii.ip = NULL;
        ii.status = DOMAIN_S_NEED_QUERY;
        db_instance_update_status(db_id, &ii, -1);
        return 1;
    }
    else if (len == 0) {
        /* Maybe the client have closed */
        loginfo(_("socket %d recv 0 byte. close socket\n"), fd);
        return 1;
    }
    logdebug(_("socket %d recv %d bytes\n"), fd, len);

    while(1) {
        int ret = ly_packet_recv(pkt, len);
        if (ret < 0) {
            logerror(_("package recv error in %s\n"), __func__);
            __print_recv_buf(buf, len);
            break;
        }

        /* currenly we only support processing a complete packet */
        if (ret == 0) {
            if (pkt->pkt_buf_received > 0) {
                loginfo(_("socket %d recv partial packet(len %d)\n"),
                           fd, pkt->pkt_buf_received);
                __print_recv_buf(buf, len);
            }
            break;
        }

        int type = ly_packet_type(pkt);
        loginfo(_("socket %d recv packet, type %d\n"), fd, type);
        /*
        if (type == PKT_TYPE_UNKNOW)
            break;
        */

        buf = ly_packet_data(pkt, &size);
        if (type == PKT_TYPE_WEB_NEW_JOB_REQUEST) {
            ly_entity_init(ent_id, LY_ENTITY_WEB);
            ret = __process_web_job(buf, size, ent_id);
            if (ret < 0)
                logerror(_("web packet process error in %s.\n"), __func__);
        }
	else if (type == PKT_TYPE_NODE_REGISTER_REQUEST) {
            ly_entity_init(ent_id, LY_ENTITY_NODE);
            ret = eh_process_node_xml(buf, ent_id);
            if (ret < 0)
                logerror(_("node packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_NODE_AUTH_REQUEST ||
                 type == PKT_TYPE_NODE_AUTH_REPLY) {
            ly_entity_init(ent_id, LY_ENTITY_NODE);
            ret = eh_process_node_auth(type == PKT_TYPE_NODE_AUTH_REPLY ?
                                       1 : 0, buf, ent_id);
            if (ret < 0)
                logerror(_("node auth packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_OSM_AUTH_REQUEST ||
                 type == PKT_TYPE_OSM_AUTH_REPLY) {
            ly_entity_init(ent_id, LY_ENTITY_OSM);
            ret = eh_process_osm_auth(type == PKT_TYPE_OSM_AUTH_REPLY ?
                                       1 : 0, buf, ent_id);
            if (ret < 0)
                logerror(_("osm auth packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_CLC_OSM_QUERY_REPLY) {
            ret = eh_process_osm_query(ly_packet_data(pkt, NULL));
            if (ret < 0)
                logerror(_("osm packet process error in %s\n"), __func__);
        }
	else if (PKT_TYPE_ENTITY_GROUP_CLC(type) ||
                 PKT_TYPE_ENTITY_GROUP_NODE(type)) {
            ret = eh_process_node_xml(buf, ent_id);
            if (ret < 0)
                logerror(_("node packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_OSM_REGISTER_REQUEST) {
            ly_entity_init(ent_id, LY_ENTITY_OSM);
            ret = eh_process_osm_register(buf, size, ent_id);
            if (ret < 0)
                logerror(_("osm packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_OSM_REPORT) {
            ret = eh_process_osm_report(buf, size, ent_id);
            if (ret < 0)
                logerror(_("osm packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_TEST_ECHO_REQUEST) {
            ret = __process_test_echo(buf, size, ent_id);
            if (ret < 0)
                logerror(_("echo packet process error in %s.\n"), __func__);
        }
        else {
            logerror(_("unrecognized packet type.\n"));
        }

        if (ly_packet_recv_done(pkt) < 0 || ret < 0) {
            logerror(_("%s return error\n"), __func__);
            return -1;
        }

        if (ret > 0)
            return ret;

        len = 0; /* continue processing data in buffer */
    }

    return 0;
}

/* start clc main work socket */
int ly_epoll_work_start(int port)
{
    if (g_efd == -1)
        return -1;

    int listener, ret = 0;
    char portstr[10];
    sprintf(portstr, "%d", port);

    listener = lyutil_create_and_bind(portstr);
    if (listener < 0) {
        logerror(_("failed create/bind port %d\n"), port);
        return -1;
    }

    ret = lyutil_make_socket_nonblocking(listener);
    if (ret < 0) {
        logerror(_("failed make port %d nonblocking\n"), port);
        goto out;
    }

    ret = listen(listener, SOMAXCONN);
    if (ret < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out;
    }

    int id = ly_entity_new(listener);
    if (id < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out;
    }
    struct epoll_event ev;
    ev.events = EPOLLIN;
    ev.data.fd = id;
    ret = epoll_ctl(g_efd, EPOLL_CTL_ADD, listener, &ev);
    if (ret < 0) {
        logerror(_("add socket to epoll error in %s.\n"), __func__);
        ly_entity_release(id);
        /* close(listener); closed in ly_entity_release */
        return -1;
        goto out;
    }
    ly_entity_init(id, LY_ENTITY_CLC);

out:
    if (ret != 0)
        close(listener);
    return ret;
}

/* events processing initialization */
int ly_epoll_init(unsigned int max_events)
{
    if (g_efd >= 0)
        return -255;

    g_efd = epoll_create(max_events);
    if (g_efd == -1)
        return -1;

    return 0;
}

/* stop and clean event processing */
int ly_epoll_close(void)
{
    if (g_efd < 0)
        return -255;

    close(g_efd);
    g_efd = -1;
    return 0;
}
