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
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <unistd.h>             /* gethostname */
#include <netdb.h>              /* struct hostent */
#include <errno.h>

#include "../luoyun/luoyun.h"

#include "lyosm.h"
#include "osmlog.h"
#include "osmutil.h"
#include "lyauth.h"
#include "lypacket.h"
#include "osmanager.h"
#include "events.h"

/* not pretty! debugging only */
static void __print_recv_buf(char *buf)
{
    int i;
    for (i=0; i<8; i++)
        logsimple("%02x ", buf[i]);
    logsimple("\n");
    LYPacketHeader h = *(LYPacketHeader *)buf;
    int type = h.type;
    int len = h.length;
    logsimple("type = %d, length = %d\n", type, len);
}

/* process OS manager query request */
static int __process_osm_query(char *buf, int size)
{
    if (size != sizeof(int32_t)) {
        logerror("unexpected osm query data length\n");
        return -1;
    }

    int req_id = *(int32_t *)buf;
    logdebug("osm query id %d\n", req_id);

    logdebug("sending osm query reply...\n");

    int status;
    if (g_c->state == OSM_STATUS_APP_RUNNING)
        status = DOMAIN_S_SERVING;
    else 
        status = DOMAIN_S_RUNNING;

    OSMConfig *c = &g_c->config;

    char pkt[100];
    sprintf(pkt, "%d %d %d %s", req_id, c->osm_tag, status,
                             g_c->osm_ip ? g_c->osm_ip : "empty");
    if (ly_packet_send(g_c->wfd, PKT_TYPE_CLC_OSM_QUERY_REPLY,
                       pkt, strlen(pkt)) < 0) {
        logerror("packet send error(%d, %d)\n", __LINE__, errno);
        return -1;
    }

    return 0;
}

/* process clc reply */
static int __process_clc_reply(char *buf, int size)
{
    if (size != sizeof(int32_t)) {
        logerror("unexpected clc packet data length\n");
        return -1;
    }

    int status = *(int32_t *)buf;

    logdebug("clc reply status %d\n", status);

    if (status == LY_S_REGISTERING_DONE_SUCCESS) {
        loginfo("osm registered successfully\n");
        g_c->state = OSM_STATUS_REGISTERED;
    }
    else {
        logwarn("osm registration failed(%d)\n", status);
        g_c->state = OSM_STATUS_UNREGISTERED;
        return 1;
    }

    
    return 0;
}

/* process authentication packets */
static int __process_work_authtication(int is_reply, void * buf, int len)
{
    if (buf == NULL || len != sizeof(AuthInfo)) {
        logerror("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    AuthInfo * ai = buf;

    int ret;
    AuthConfig * ac = &g_c->auth;

    if (is_reply) {
        if (g_c->state != OSM_STATUS_AUTHENTICATING) {
            logerror("error in %s(%d)\n", __func__, __LINE__);
            return -1;
        }
        ret = lyauth_verify(ac, ai->data, LUOYUN_AUTH_DATA_LEN);
        if (ret < 0) {
            logerror("error in %s(%d)\n", __func__, __LINE__);
            return -1;
        }
        if (ret) {
            loginfo("chanllenge verification passed\n");
            g_c->state = OSM_STATUS_AUTHENTICATED;
        }
        else {
            logwarn("chanllenge verification failed\n");
            g_c->state = OSM_STATUS_UNAUTHENTICATED;
            return 1;
        }
            
        return 0;
    }

    ret = lyauth_answer(ac, ai->data, LUOYUN_AUTH_DATA_LEN);
    if (ret < 0) {
        logerror("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }

    /* send answer back */
    if (ly_packet_send(g_c->wfd, PKT_TYPE_OSM_AUTH_REPLY,
                       ai, sizeof(AuthInfo)) < 0) {
        logerror("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }

    /* authetication completed */
    if (ly_osm_register() != 0)
        logerror("failed registering osm in %s\n", __func__);
    return 0;
}

/* process unicast join request */
static int __process_work_join(char * buf)
{
    g_c->state = OSM_STATUS_INIT;
    if (ly_osm_register() != 0)
        logerror("failed registering osm in %s\n", __func__);
    return 0;
}

/* process echo request */
static int __process_work_echo(char * buf, int size)
{
    logdebug("sending echo reply ...\n");
    logdebug("%s\n", buf);
    return ly_packet_send(g_c->wfd, PKT_TYPE_TEST_ECHO_REPLY, buf, size);
}

/*
** work socket EPOLLIN event processing
** return -1 : error
**         0 : success, nothing expected to be followed
**         1 : success, socket closed
**/
int ly_epoll_work_recv(void)
{
    if (g_c == NULL || g_c->wfd < 0)
        return -255;

    OSMConfig *c = &g_c->config;

    LYPacketRecv * pkt = &g_c->wfd_pkt;
    if (pkt == NULL)
        return -255;

    int size;
    void * buf = ly_packet_buf(pkt, &size);
    if (buf == NULL) {
        logerror("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    if (size == 0) {
        logwarn("ly_packet_buf returns 0 size buffer\n");
        return 0;
    }

    int ret = recv(g_c->wfd, buf, size, 0);
    if (ret == -1) {
        logerror("recv error(%d) in %s. close socket\n", errno, __func__);
        return -1;
    }
    else if (ret == 0) {
        /* Maybe the client have closed */
        loginfo("recv 0 byte. close socket.\n");
        return 1;
    }
    logdebug("recv %d bytes received\n", ret);
    if (c->debug)
        __print_recv_buf(buf);

    while(1) {
        ret = ly_packet_recv(pkt, ret);
        if (ret == 0) {
            /* continue */
            return 0;
        }
        else if (ret < 0) {
            logerror("error in %s(%d)\n", __func__, __LINE__);
            return -1;
        }

        int len; 
        buf = ly_packet_data(pkt, &len);
        int type = ly_packet_type(pkt);
        if (type == PKT_TYPE_JOIN_REQUEST) {
            ret = __process_work_join(buf);
            if (ret < 0)
                logerror("string packet process error in %s\n", __func__);
        }
        else if (type == PKT_TYPE_TEST_ECHO_REQUEST) {
            ret = __process_work_echo(buf, len);
            if (ret < 0)
                logerror("echo packet process error in %s\n", __func__);
        }
        else if (type == PKT_TYPE_OSM_AUTH_REQUEST ||
                 type == PKT_TYPE_OSM_AUTH_REPLY) {
            ret = __process_work_authtication(
                    type == PKT_TYPE_OSM_AUTH_REPLY ? 1 : 0, buf, len);
            if (ret < 0)
                logerror("auth packet process error in %s\n", __func__);
        }
        else if (type == PKT_TYPE_OSM_REGISTER_REPLY) {
            ret = __process_clc_reply(buf, len);
            if (ret < 0)
                logerror("clc reply packet process error in %s\n", __func__);
        }
        else if (type == PKT_TYPE_CLC_OSM_QUERY_REQUEST) {
            ret = __process_osm_query(buf, len);
            if (ret < 0)
                logerror("osm query packet process error in %s\n", __func__);
        }
        else {
            logerror("unrecognized packet type.\n");
        }

        if (ly_packet_recv_done(pkt) < 0 || ret < 0) {
            logerror("error in %s(%d)\n", __func__, __LINE__);
            return -1;
        }

        if (ret > 0)
            return ret;

        ret = 0; /* continue processing data in buffer */
    }

    return 0;
}

int ly_osm_report(int status)
{
    if (g_c->wfd < 0)
        return -1;

    if (ly_packet_send(g_c->wfd, PKT_TYPE_OSM_REPORT,
                       &status, sizeof(int)) < 0) {
        logerror("packet send error(%d, %d)\n", __LINE__, errno);
        return -1;
    }

    return 0;
}

/* register to clc */
int ly_osm_register()
{
    if (g_c == NULL || g_c->wfd < 0)
        return -255;

    OSMConfig *c = &g_c->config;
    AuthConfig *ac = &g_c->auth;
    
    if (g_c->state == OSM_STATUS_INIT && ac->secret) {
        /* request challenging */
        if (lyauth_prepare(ac) < 0) {
            logerror("error in %s(%d)\n", __func__, __LINE__);
            return -1;
        }
        
        AuthInfo ai;
        ai.tag = c->osm_tag;
        bzero(ai.data, LUOYUN_AUTH_DATA_LEN);
        strncpy((char *)ai.data, ac->challenge, LUOYUN_AUTH_DATA_LEN);
        if (ly_packet_send(g_c->wfd, PKT_TYPE_OSM_AUTH_REQUEST,
                           &ai, sizeof(AuthInfo)) < 0) {
            logerror("error in %s(%d)\n", __func__, __LINE__);
            return -1;
        }
        g_c->state = OSM_STATUS_AUTHENTICATING;
        return 0;
    }

    loginfo("send register request...\n");

    if (g_c->state >= OSM_STATUS_UNAUTHENTICATED &&
        g_c->state >= OSM_STATUS_AUTHENTICATED)
        g_c->state = OSM_STATUS_UNREGISTERED;

    char pkt[100];
    sprintf(pkt, "%d %d %s", c->osm_tag, g_c->state,
                             g_c->osm_ip ? g_c->osm_ip : "empty");
    if (ly_packet_send(g_c->wfd, PKT_TYPE_OSM_REGISTER_REQUEST,
                       pkt, strlen(pkt)) < 0) {
        logerror("packet send error(%d, %d)\n", __LINE__, errno);
        return -1;
    }

    if (g_c->state == OSM_STATUS_UNREGISTERED)
        g_c->state = OSM_STATUS_REGISTERING;

    return 0;
}

/* work socket registration */
int ly_epoll_work_register(void)
{
    if (g_c == NULL || g_c->efd < 0)
        return -255;

    if (g_c->wfd >= 0)
        ly_epoll_work_close();

    /* connect to clc */
    int fd = lyutil_connect_to_host(g_c->clc_ip, g_c->clc_port);
    if (fd <= 0) {
        logerror("connect_to_host %s %d error.\n",
                  g_c->clc_ip, g_c->clc_port);
        return -1;
    }

    if (g_c->osm_ip == NULL) {
        g_c->osm_ip = lyutil_get_local_ip(fd);
        if (g_c->osm_ip == NULL) {
            logerror("get local ip error in %s\n", __func__);
            close(fd);
            return -1;
        }
    }

    /* make socket nonblocking */
    int ret = lyutil_make_socket_nonblocking(fd);
    if (ret != 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        close(fd);
        return -1;
    }

    /* keep alive */
    if (lyutil_set_keepalive(fd, LY_OSM_KEEPALIVE_INTVL,
                                 LY_OSM_KEEPALIVE_INTVL,
                                 LY_OSM_KEEPALIVE_PROBES) < 0) {
        logerror("error in %s(%d)\n", __func__, __LINE__);
        close(fd);
        return -1;
    }

    /* prepare packet receive structure */
    ret = ly_packet_init(&g_c->wfd_pkt);
    if (ret < 0 ) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        close(fd);
        return ret;
    }

    /* register socket */
    struct epoll_event ev;
    /* ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP; */
    ev.events = EPOLLIN;
    ev.data.fd = fd;
    ret = epoll_ctl(g_c->efd, EPOLL_CTL_ADD, fd, &ev);
    if (ret < 0) {
        logerror("add work socket to epoll error\n");
        close(fd);
        ly_packet_cleanup(&g_c->wfd_pkt);
        return ret;
    }

    loginfo("registering work socket(%d)\n", fd);
    g_c->wfd = fd;
    return 0;
}

static int  __process_mcast_string(char * str, char * ip, int * port)
{
    if (str == NULL || ip == NULL || port == NULL)
        return -255;

    char s[MAX_IP_LEN+20], j[10];
    sprintf(s, "%%9s %%%ds %%d\n", MAX_IP_LEN);
    if (sscanf(str, s, j, ip, port) != 3 || strcmp(j, "join") != 0) {
        logwarn("string message unrecoginized at %d.\n", __LINE__);
        logdebug(str);
        return -1;
    }
    logdebug("join %s %d\n", ip, *port);
    return 0;
}

/* 
** receive/check mcast data
** upon successful return, clc_ip/clc_port/host_ip are recorded in g_c
** return -1 : error
**         0 : success, nothing expected to be followed
**         1 : success, registering should be followed
*/
int ly_epoll_mcast_recv()
{
    if (g_c == NULL || g_c->mfd < 0 || g_c->mfd_cmsg == NULL)
        return -255;

    struct msghdr msg;
    struct iovec s; 
    int size;
    s.iov_base = ly_packet_buf(&g_c->mfd_pkt, &size);
    if (s.iov_base == NULL) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        return -255;
    }
    s.iov_len = size;

    msg.msg_name = NULL;
    msg.msg_namelen = 0;
    msg.msg_iov = &s;
    msg.msg_iovlen = 1;
    msg.msg_control = g_c->mfd_cmsg;
    msg.msg_controllen = g_c->mfd_cmsg_size;
    int datalen = recvmsg(g_c->mfd, &msg, 0);
    if (datalen < 0) {
        if (errno == EAGAIN)
            return 0;
        logerror("recvmsg returns error(%d) in %s\n", errno, __func__);
        return -1;
    }
    logdebug("recvmsg %d bytes received\n", datalen);

    char ip[MAX_IP_LEN];
    int port = 0;
    int ret = ly_packet_recv(&g_c->mfd_pkt, datalen);
    if (ret == 0) {
        logerror("mcast packet partially received. ignore.\n");
        ly_packet_recv_done(&g_c->mfd_pkt);
        return 0;
    }
    else if (ret < 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
    }
    else if (ly_packet_type(&g_c->mfd_pkt) == PKT_TYPE_JOIN_REQUEST) {
        ret = __process_mcast_string(ly_packet_data(&g_c->mfd_pkt, NULL), ip, &port);
        if (ret < 0)
            logerror("string packet process error in %s.\n", __func__);
    }
    else {
        logwarn("unrecognized mcast msg received.\n");
        ret = -1;
    }
    if (ly_packet_recv_done(&g_c->mfd_pkt) < 0 || ret < 0)
        return -1;

    char localip[MAX_IP_LEN];
    if (msg.msg_controllen > 0) {
        struct cmsghdr *h = msg.msg_control;
        if (h->cmsg_type != IP_PKTINFO) {
            logwarn("unrecognized mcast msg control data received %d\n",
                     h->cmsg_type); 
            return -1;
        }
        struct in_pktinfo * i = (struct in_pktinfo *)((char*)h+sizeof(*h));
        char index[IF_NAMESIZE];
        if (if_indextoname(i->ipi_ifindex, index))
            strcpy(localip, inet_ntoa(i->ipi_spec_dst));

        /* do nothing if they are same as we already have */
        if (g_c->clc_ip && strcmp(g_c->clc_ip, ip) == 0 &&
            g_c->clc_port == port ) {
            logdebug("same join message received\n");
            return 0;
        }

        /* logging the result */
        logwarn("New clc host info received(%s %d %s)\n", ip, port, localip);

        /* update clc info */
        if (g_c->clc_ip == NULL) {
            g_c->clc_ip = strdup(ip);
            g_c->clc_port = port;
            if (g_c->osm_ip)
                free(g_c->osm_ip);
            g_c->osm_ip = strdup(localip);
            logwarn("New clc host info will be used\n");
            return 1; /* (re)register is needed */
        }
        logwarn("New clc host info ignored\n");
        return 0;
    }

    return -2; /* got data, but not useful */
}

/* curtosy of www.tenouk.com */
int ly_epoll_mcast_register()
{
    if (g_c == NULL || g_c->efd < 0 || g_c->mfd != -1)
        return -255;

    int ret = 0;
    OSMConfig *c = &g_c->config;

    /* Create a datagram socket on which to receive. */
    int sd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sd < 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        return -1;
    }

    /* Enable SO_REUSEADDR */
    int reuse = 1;
    if (setsockopt (sd, SOL_SOCKET, SO_REUSEADDR, (char *) &reuse, sizeof(reuse)) < 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        close(sd);
        return -1;
    }

    /* Bind to the proper port number with the IP address specified as INADDR_ANY. */
    struct sockaddr_in localSock;
    memset((char *) &localSock, 0, sizeof(localSock));
    localSock.sin_family = AF_INET;
    localSock.sin_port = htons(c->clc_mcast_port);
    localSock.sin_addr.s_addr = INADDR_ANY;
    if (bind(sd, (struct sockaddr *) &localSock, sizeof(localSock))) {
        logerror("binding datagram socket on port %d error in %s",
                 c->clc_mcast_port, __func__);
        close(sd);
        return -1;
    }

    /* make socket nonblocking */
    ret = lyutil_make_socket_nonblocking(sd); 
    if (ret != 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        close(sd);
        return -1;
    }

    /* Join the multicast group on INADDR_ANY interface */
    struct ip_mreq group;
    group.imr_multiaddr.s_addr = inet_addr(c->clc_mcast_ip);
    group.imr_interface.s_addr = INADDR_ANY;
    if (setsockopt (sd, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char *) &group, sizeof(group)) < 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        close(sd);
        return -1;
    }

    /* enable receiving control message */
    int yes = 1;
    if (setsockopt (sd, IPPROTO_IP, IP_PKTINFO, (char *) &yes, sizeof(yes)) < 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        close(sd);
        return -1;
    }

    /* prepare packet receive structure */
    if (ly_packet_init(&g_c->mfd_pkt) < 0 ) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        close(sd);
        return -1;
    }
    if (g_c->mfd_cmsg == NULL) {
        g_c->mfd_cmsg_size = sizeof(struct cmsghdr)+sizeof(struct in_pktinfo);
        g_c->mfd_cmsg = malloc(g_c->mfd_cmsg_size);
        if (g_c->mfd_cmsg == NULL) {
            logerror("error in %s(%d).\n", __func__, __LINE__);
            ret = -1;
            goto out;
        }
    }

    /* register event */
    struct epoll_event ev;
    ev.events = EPOLLIN;
    ev.data.fd = sd;
    ret = epoll_ctl(g_c->efd, EPOLL_CTL_ADD, sd, &ev);
    if (ret < 0) {
        logerror("error in %s(%d).\n", __func__, __LINE__);
        ret = -1;
        goto out;
    }
    loginfo("registering mcast event done(%d)\n", sd);

out:
    if (ret < 0){
        close(sd);
        ly_epoll_mcast_close();
    }
    else
        g_c->mfd = sd;
    return ret;
}

/* mcast socket down */
int ly_epoll_mcast_close(void)
{
    if (g_c == NULL)
        return -255;

    if (g_c->mfd >= 0)
        close(g_c->mfd);
    g_c->mfd = -1;
    
    ly_packet_cleanup(&g_c->mfd_pkt);

    if (g_c->mfd_cmsg != NULL) {
        free(g_c->mfd_cmsg);
        g_c->mfd_cmsg = NULL;
    }

    return 0;
}

/* work socket down */
int ly_epoll_work_close(void)
{
    if (g_c == NULL)
        return -255;

    if (g_c->wfd >= 0)
        close(g_c->wfd);
    g_c->wfd = -1;

    ly_packet_cleanup(&g_c->wfd_pkt);

    g_c->state = OSM_STATUS_UNKNOWN;
    return 0;
}

/* events processing initialization */
int ly_epoll_init(unsigned int max_events)
{
    if (g_c == NULL)
        return -255;

    if (g_c->efd >= 0)
        close(g_c->efd);

    g_c->efd = epoll_create(max_events);
    if (g_c->efd == -1){
        logerror("error in %s(%d).\n", __func__, __LINE__);
        return -1;
    }

    return 0;
}

/* stop and clean event processing */
int ly_epoll_close(void)
{
    if (g_c == NULL || g_c->efd < 0)
        return -255;

    ly_epoll_mcast_close();
    ly_epoll_work_close();

    close(g_c->efd);
    g_c->efd = -1;
    return 0;
}

