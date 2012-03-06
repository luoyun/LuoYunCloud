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
#include <arpa/inet.h>
#include <net/if.h>
#include <unistd.h>             /* gethostname */
#include <netdb.h>              /* struct hostent */
#include <errno.h>

#include <sys/epoll.h>
/* in RHEL5, EPOLLRDHUP is not defined */
#ifndef EPOLLRDHUP
#define EPOLLRDHUP 0x2000
#endif

#include "luoyun.h"
#include "lyutil.h"
#include "lypacket.h"
#include "lyxml.h"

#define MAX_EVENTS 10

int g_efd = -1;
int g_wfd = -1;
int g_nfd = -1;
LYPacketRecv g_nfd_pkt;

int g_state = 0;

static void __print_recv_buf(char *buf)
{
    int i;
    for (i=0; i<8; i++)
        printf("%02x ", buf[i]);
    printf("\n");
    LYPacketHeader h = *(LYPacketHeader *)buf;
    int type = h.type;
    int len = h.length;
    printf("type = %d, length = %d\n", type, len);
}

void print_node_info(NodeInfo * N)
{
    printf("node = {\n"
           "\tstatus = %d\n"
           "\thostname = %s\n"
           "\tip = %s\n"
           "\tport = %d\n"
           "\tarch = %d\n"
           "\thypervisor = %d\n"
           "\tnetwork_type = %d\n"
           "\tmax_memory = %d\n"
           "\tmax_cpus = %d\n"
           "\tcpu_model = %s\n"
           "\tcpu_mhz = %d\n"
           "\tload_average = %d\n" "\tfree_memory = %d\n"
           /*"\tcreated = %d\n" */
           /*"\tupdated = %d\n" */
           "}\n",
           N->status, N->hostname, N->ip, N->port,
           N->arch, N->hypervisor, N->network_type,
           N->max_memory, N->max_cpus, N->cpu_model,
           N->cpu_mhz, N->load_average, N->free_memory);
}

/* events processing initialization */
int epoll_init(unsigned int max_events)
{
    if (g_efd >= 0)
        close(g_efd);

    g_efd = epoll_create(max_events);
    if (g_efd == -1) {
        printf("epoll_create failed in %s.\n", __func__);
        return -1;
    }

    return 0;
}

int mcast_send_join(int port)
{
    struct in_addr localInterface;
    struct sockaddr_in groupSock;
    int sd, ret = 0;

    char databuf1[400];
    char databuf[400];
#if 1 
    sprintf(databuf1, "join 192.168.1.107 %d", port);
    int datalen = strlen(databuf1);
    databuf[0] = 2;
#else
    if (lyxml_data_join(1, "192.168.1.107", port, databuf1, 400) == NULL) {
        printf("lyxml_data_join error\n");
        return -1;
    }
    int datalen = strlen(databuf1);
    databuf[0] = 1;
#endif
    printf("%s\n", databuf1);
    printf("%d\n", datalen);
    for (int i=0; i<sizeof(int); i++)
        databuf[i+1] = *((char *)&datalen+sizeof(int)-i-1);
    memcpy(&databuf[sizeof(int)+1], databuf1, datalen);
    datalen += sizeof(int)+1;
    printf("%2x %2x %2x %2x %2x\n", databuf[0], (unsigned char)databuf[1], databuf[2], databuf[3], databuf[4]);

    /* Create a datagram socket on which to send. */
    sd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sd < 0) {
        perror("Opening datagram socket error");
        return -1;
    }
    else
        printf("Opening the datagram socket...OK.\n");

    /* Initialize the group sockaddr structure */
    memset((char *) &groupSock, 0, sizeof(groupSock));
    groupSock.sin_family = AF_INET;
    groupSock.sin_addr.s_addr = inet_addr("228.0.0.1");
    groupSock.sin_port = htons(1369);

    /* Set local interface for outbound multicast datagrams. */
    /* The IP address specified must be associated with a local, */
    /* multicast capable interface. */
    localInterface.s_addr = inet_addr("192.168.1.107");
    if (setsockopt
        (sd, IPPROTO_IP, IP_MULTICAST_IF, (char *) &localInterface,
         sizeof(localInterface)) < 0) {
        perror("Setting local interface error");
        ret = -1;
        goto out;
    }
    else
        printf("Setting the local interface...OK\n");

    /* Send a message to the multicast group specified by the */
    /* groupSock sockaddr structure. */
    /*int datalen = 1024; */
# if 0
    if (sendto
        (sd, databuf, datalen, 0, (struct sockaddr *) &groupSock,
         sizeof(groupSock)) < 0) {
        perror("Sending datagram message error");
        ret = -1;
        goto out;
    }
    else
        printf("Sending datagram message...OK\n");
#else
    unsigned int d = PKT_TYPE_JOIN_REQUEST;
    sendto(sd, &d, sizeof(d), 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
    d = 0;
    sendto(sd, &d, sizeof(d), 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
    d = 0;
    sendto(sd, &d, sizeof(d), 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
    d = 0;
    sendto(sd, &d, sizeof(d), 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
    d = (unsigned char)strlen(databuf1);
    sendto(sd, &d, sizeof(d), 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
    d = PKT_TYPE_JOIN_REQUEST;
    sendto(sd, &d, sizeof(d), 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
    d = strlen(databuf1);
    sendto(sd, databuf1, d, 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
    *(int *)databuf = PKT_TYPE_JOIN_REQUEST;
    *((int *)databuf + 1) = d;
    sprintf(&databuf[8], "%s", databuf1);
    sendto(sd, databuf, d+8, 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
#endif
  out:
    close(sd);
    return ret;
}

int epoll_work_start(int port)
{
    if (g_efd == -1 || g_wfd != -1)
        return -1;

    int listener, ret = 0;
    char portstr[10];
    sprintf(portstr, "%d", port);

    listener = lyutil_create_and_bind(portstr);
    if (listener < 0) {
        printf("failed create/bind port %d\n", port);
        return -1;
    }

    ret = lyutil_make_socket_nonblocking(listener);
    if (ret < 0) {
        printf("failed make port %d nonblocking\n", port);
        goto out;
    }

    ret = listen(listener, SOMAXCONN);
    if (ret < 0) {
        printf("failed listening on work socket %s\n", __func__);
        goto out;
    }

    struct epoll_event ev;
    ev.events = EPOLLIN | EPOLLET;
    ev.data.fd = listener;
    ret = epoll_ctl(g_efd, EPOLL_CTL_ADD, listener, &ev);
    if (ret < 0) {
        printf("Add listener to epoll error in %s.\n", __func__);
        goto out;
    }

  out:
    if (ret == 0)
        g_wfd = listener;
    else
        close(listener);
    return ret;
}

int epoll_work_recv(void)
{
    if (g_efd == -1 || g_wfd == -1)
        return -1;

    struct sockaddr in_addr;
    socklen_t in_len;
    int infd;

    in_len = sizeof(in_addr);
    infd = accept(g_wfd, &in_addr, &in_len);
    if (infd == -1) {
        if ((errno == EAGAIN) || (errno == EWOULDBLOCK)) {
            /* We have processed all incoming connections. */
            return 0;
        }
        else {
            printf("unexpected accept error in %s", __func__);
            return errno;
        }
    }

    char hbuf[NI_MAXHOST], sbuf[NI_MAXSERV];
    int ret = getnameinfo(&in_addr, in_len,
                          hbuf, sizeof hbuf,
                          sbuf, sizeof sbuf,
                          NI_NUMERICHOST | NI_NUMERICSERV);
    if (ret == 0)
        printf("Accepted connection on descriptor %d from %s:%s\n", infd,
               hbuf, sbuf);

    char request[1500];
    bzero(request, 1500);
    memset(request, 0, sizeof(request));
    ret = recv(infd, request, sizeof(request), 0);
    if (ret < 0) {
        printf("Recv request header failed.\n");
        close(infd);
        return -1;
    }
    printf("%d received\n%d %d %s\n", ret, *(int *)&request[0], 
                         *(unsigned int*)&request[4],
                         request + 8);

    char * idstr = xml_xpath_prop_from_str(request + 8, "/luoyun/request", "id");
    if (idstr)
        printf("id = %s\n", idstr);
    else {
        printf("can't get idstr\n");
        return -1;
    }

    printf("sending reply\n");
    LYReply r;
    r.req_id = atoi(idstr);
    r.from = LY_ENTITY_NODE;
    r.to = LY_ENTITY_CLC;
    r.status = LY_S_FINISHED_SUCCESS;
    r.msg = "success";
    char * response = lyxml_data_reply(&r, NULL, 0);
    ly_packet_send(infd, PKT_TYPE_NODE_REGISTER_REPLY,
                   response, strlen(response));
    free(response);

#if 0
    //shutdown(infd, SHUT_RDWR);
    close(infd);
#else
    /* prepare packet receive structure */
    ret = ly_packet_init(&g_nfd_pkt);
    if (ret < 0 ) {
        printf("ly_packet_init error in  %s\n", __func__);
        close(infd);
        return -1;
    }
    struct epoll_event ev;
    ev.events = EPOLLIN;
    ev.data.fd = infd;
    ret = epoll_ctl(g_efd, EPOLL_CTL_ADD, infd, &ev);
    if (ret < 0) {
        printf("Add node to epoll error in %s.\n", __func__);
        ly_packet_cleanup(&g_nfd_pkt);
        close(infd);
        return -1;
    }
    g_nfd = infd;
#endif
    if (g_state == 1)
        g_state = 2;

    return 0;
}

static int __process_node_echo(char * buf, int size)
{
    printf("echo reply size %d, %s\n", size, buf);
    return 0;
}

int epoll_node_recv()
{
    if (g_nfd < 0)
        return -255;

    LYPacketRecv * pkt = &g_nfd_pkt;

    int size;
    void * buf = ly_packet_buf(pkt, &size);
    if (buf == NULL) {
        printf("ly_packet_buf returns NULL buffer\n");
        return -1;
    }
    if (size == 0) {
        printf("ly_packet_buf returns 0 size buffer\n");
        return 0;
    }

    int ret = recv(g_nfd, buf, size, 0);
    if (ret == -1) {
        printf("recv error(%d) in %s. close socket.\n", errno, __func__);
        return -1;
    }
    else if (ret == 0) {
        /* Maybe the client have closed */
        printf("recv 0 byte. close socket.\n");
        return 1;
    }
    printf("recv %d bytes received\n", ret);
    __print_recv_buf(buf);

    while(1) {
        ret = ly_packet_recv(pkt, ret);
        if (ret == 0) {
            printf("ly_packet_recv return 0. continue receiving ...\n");
            return 0;
        }
        else if (ret < 0) {
            printf("package recv error in %s.\n", __func__);
        }
        else if (ly_packet_type(pkt) == PKT_TYPE_TEST_ECHO_REPLY) {
            buf = ly_packet_data(pkt, &ret);
            ret = __process_node_echo(buf, ret);
            if (ret < 0)
                printf("node packet process error in %s.\n", __func__);
        }
        else {
            printf("unrecognized packet type.\n");
        }
        if (ly_packet_recv_done(pkt) < 0 || ret < 0) {
            printf("%s return error\n", __func__);
            return -1;
        }
        ret = 0;
    }

    return 0;
}

int start_echo_test(int id)
{
    if (g_nfd < 0)
        return -1;

    struct mytest {
        int pkt_len;
        int header_len;
        char * data;
        int data_len;
    } t[50];

    int i;
    char str1[26];
    for (i = 0;i < 26; i++)
        str1[i] = 'a' + i;

    char str2[37];
    for (i = 0;i < 26; i++)
        str2[i] = 'A' + i;
    for (;i < 36; i++)
        str2[i] = '0' + i - 26;
    str2[i] = 0;

#define myassign(t,p1, p2, p3, p4) {struct mytest p = {p1, p2, p3, p4};t=p;}
    i = 0;
    myassign(t[i++], 26, sizeof(LYPacketHeader), (char *)str1, 26)
    myassign(t[i++], 26, 4, str1, 0)
    myassign(t[i++], 26, sizeof(LYPacketHeader)-4, str1, 20)
    myassign(t[i++], 26, 0, &str1[20], 6)
    myassign(t[i++], 26, sizeof(LYPacketHeader), str2, 8)

    if (id < i) {
        printf("sending echo request %d ...\n", id);
        LYPacketHeader header;
        header.type = PKT_TYPE_TEST_ECHO_REQUEST;
        header.length = t[id].pkt_len;

        struct iovec s[2];
        s[0].iov_base = (char *)&header+ (t[id].data_len?sizeof(LYPacketHeader)-t[id].header_len:0);
        s[0].iov_len = t[id].header_len;
        s[1].iov_base = t[id].data;
        s[1].iov_len = t[id].data_len;

        struct msghdr msg;
        msg.msg_name = NULL;
        msg.msg_namelen = 0;
        msg.msg_iov = s;
        msg.msg_iovlen = 2;
        msg.msg_control = NULL;
        msg.msg_controllen = 0;
        int datalen = sendmsg(g_nfd, &msg, 0);
        if (datalen < 0) 
            return -1;
        return 0;
    }

    myassign(t[i++], 10, 2, &str2[8], 20)
    if (id < i) {
        printf("sending echo request %d ...\n", id);
        LYPacketHeader header;
        header.type = PKT_TYPE_TEST_ECHO_REQUEST;
        header.length = t[id].pkt_len;

        struct iovec s[2];
        s[0].iov_base = t[id].data;
        s[0].iov_len = t[id].data_len - t[id].header_len;
        s[1].iov_base = (char *)&header;
        s[1].iov_len = t[id].header_len;

        struct msghdr msg;
        msg.msg_name = NULL;
        msg.msg_namelen = 0;
        msg.msg_iov = s;
        msg.msg_iovlen = 2;
        msg.msg_control = NULL;
        msg.msg_controllen = 0;
        int datalen = sendmsg(g_nfd, &msg, 0);
        if (datalen < 0)
            return -1;
        return 0;
    }

    myassign(t[i++], 10, sizeof(LYPacketHeader)-2, &str2[26], 10)
    if (id < i) {
        printf("sending echo request %d ...\n", id);
        LYPacketHeader header;
        header.type = PKT_TYPE_TEST_ECHO_REQUEST;
        header.length = t[id].pkt_len;

        struct iovec s[2];
        s[0].iov_base = (char *)&header+sizeof(LYPacketHeader)-t[id].header_len;
        s[0].iov_len = t[id].header_len;
        s[1].iov_base = t[id].data;
        s[1].iov_len = t[id].data_len;

        struct msghdr msg;
        msg.msg_name = NULL;
        msg.msg_namelen = 0;
        msg.msg_iov = s;
        msg.msg_iovlen = 2;
        msg.msg_control = NULL;
        msg.msg_controllen = 0;
        int datalen = sendmsg(g_nfd, &msg, 0);
        if (datalen < 0)
            return -1;
        return 0;
    }


    return 100;
}

int main(int argc, char **argv)
{
    int ret = 0;

    if (epoll_init(MAX_EVENTS) != 0) {
        printf("epoll_init failed\n");
        return -1;
    }

    if (epoll_work_start(1369) != 0) {
        ret = -1;
        printf("epoll_start_server failed\n");
        goto out;
    }

    /* start main event driven loop */
    int i, n;
    int testid = 0;
    struct epoll_event events[MAX_EVENTS];
    while (ret != -1) {
        if (g_state == 0) {
            if (mcast_send_join(1369) != 0) {
                printf("mcast_send_join error\n");
                break;
            }
            g_state = 1;
        }
        else if (g_state == 2) {
            printf("sleep 2 seconds before start echo test\n");
            sleep(2);
            ret = start_echo_test(testid++);
            if (ret < 0) {
                printf("start_echo_test error\n");
                break;
            }
            else if (ret == 100){
                printf("test done\n");
                break;
            }
        }

        n = epoll_wait(g_efd, events, MAX_EVENTS, 1000);
        for (i = 0; i < n; i++) {
            if (events[i].events & EPOLLIN && events[i].data.fd == g_wfd) {
                printf("g_wfd has data in.\n");
                if (epoll_work_recv() != 0) {
                    printf("epoll_work_recv error\n");
                    ret = -1;
                    break;
                }
            }
            else if (events[i].events & EPOLLIN && events[i].data.fd == g_nfd) {
                printf("g_nfd has data in.\n");
                if (epoll_node_recv() != 0) {
                    printf("epoll_node_recv error\n");
                    ret = -1;
                    break;
                }
            }
            else if (events[i].events & EPOLLRDHUP &&
                     events[i].data.fd == g_wfd) {
                printf("g_wfd got hup. ???\n");
                ret = -1;
                break;
            }
            else if (events[i].events & EPOLLRDHUP &&
                     events[i].data.fd == g_nfd) {
                printf("g_nfd got hup. \n");
                ret = -1;
                break;
            }
            else {
                printf("unexpected event(%d, %d). quit\n",
                       events[i].events, events[i].data.fd);
                ret = -1;
                break;
            }
        }
    }

  out:
    if (g_efd != -1)
        close(g_efd);
    if (g_wfd != -1)
        close(g_wfd);
    if (g_nfd != -1) {
        close(g_nfd);
        ly_packet_cleanup(&g_nfd_pkt);
    }
    return 0;
}
