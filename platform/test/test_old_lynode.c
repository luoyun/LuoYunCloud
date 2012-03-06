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

#define MAX_EVENTS 10

int g_efd = -1;
int g_wfd = -1;
int g_kfd = -1;

int g_state = 0;


int register_request_process(int infd, LyRequest * request);

void print_node_info(ComputeNodeInfo * N)
{
    printf("node = {\n"
           "\tstatus = %d\n"
           "\thostname = %s\n"
           "\tip = %s\n"
           "\tport = %d\n"
           "\tarch = %d\n"
           "\thypervisor = %d\n"
           "\tnetwork_type = %d\n"
           "\tmax_memory = %ld\n"
           "\tmax_cpus = %d\n"
           "\tcpu_model = %s\n"
           "\tcpu_mhz = %d\n"
           "\tload_average = %d\n" "\tfree_memory = %ld\n"
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

    char databuf[100];
    sprintf(databuf, "join 192.168.1.107 %d", port);
    int datalen = sizeof(databuf);

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
    if (sendto
        (sd, databuf, datalen, 0, (struct sockaddr *) &groupSock,
         sizeof(groupSock)) < 0) {
        perror("Sending datagram message error");
        ret = -1;
        goto out;
    }
    else
        printf("Sending datagram message...OK\n");

    if (g_state == 0)
        g_state = 1;
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

    listener = create_and_bind(portstr);
    if (listener < 0) {
        printf("failed create/bind port %d\n", port);
        return -1;
    }

    ret = make_socket_non_blocking(listener);
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

    LyRequest request;
    memset(&request, 0, sizeof(request));
    if (ly_recv(infd, &request, sizeof(LyRequest), 0, RECV_TIMEOUT)) {
        printf("Recv request header failed.\n");
        close(infd);
        return -1;
    }

    if (request.type == RQTYPE_REGISTER) {
        printf("keepalive message received\n");
        if (register_request_process(infd, &request) != 0) {
            printf("register_request_recv error\n");
            close(infd);
            return -1;
        }
        g_kfd = infd;
    }
    else {
        printf("keepalive received unrecognized message(%d)\n",
               request.type);
        close(infd);
        return -1;
    }

    return 0;
}

int register_request_process(int infd, LyRequest * request)
{
    int ret;

    if (request->length != sizeof(ComputeNodeInfo)) {
        printf
            ("The length of request data(%d) and ComputeNodeInfo(%ld) doest not match.\n",
             request->length, sizeof(ComputeNodeInfo));
        return -1;
    }

    ComputeNodeInfo nitem;
    if (ly_recv(infd, &nitem, sizeof(ComputeNodeInfo), 0, RECV_TIMEOUT)) {
        printf("Recv register request data failed.\n");
        ret = -1;
        goto out;
    }
    else {
        printf("Recv register request data success.\n");
        print_node_info(&nitem);
    }

    LyRespond respond;
    respond.length = 0;
    respond.status = RESPOND_STATUS_OK;
    ret = send(infd, &respond, sizeof(LyRespond), 0);
    if (ret == -1) {
        printf("Send respond to compute node error.\n");
        ret = -1;
        goto out;
    }

    struct epoll_event ev;
    ev.data.fd = infd;
    ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP;
    ret = epoll_ctl(g_efd, EPOLL_CTL_ADD, infd, &ev);
    if (ret == -1) {
        printf("Add keep alive socket to epoll error.\n");
        ret = -1;
        goto out;
    }
    printf("keepalive socket registered\n");

    if (g_state == 1)
        g_state = 2;
    return 0;
  out:
    return ret;
}

int epoll_keepalive_recv(void)
{
    printf("epoll_keepalive_recv called. don't know how to handle.\n");
    return -1;
}

int start_test_domain()
{
    char *node_ip = "192.168.1.107";
    int node_port = 3260;

    printf("connecting %s:%d \n", node_ip, node_port);
    int sfd;
    sfd = connect_to_host(node_ip, node_port);
    if (sfd <= 0) {
        printf("Connect to %s:%d failed.\n", node_ip, node_port);
        return -1;
    }

    printf("sending request ...\n");
    LyRequest request;
    request.type = RQTYPE_DOMAIN_CONTROL;
    request.from = RQTARGET_CONTROL;
    request.length = sizeof(DomainControlData);
    if (ly_send(sfd, &request, sizeof(LyRequest), 0, SEND_TIMEOUT)) {
        printf("Send domain control request header failed.\n");
        close(sfd);
        return -1;
    }

    printf("sending command ...\n");
    DomainControlData dcd;
    dcd.id = 1;
    dcd.action = LA_DOMAIN_RUN;
    if (ly_send(sfd, &dcd, sizeof(DomainControlData), 0, SEND_TIMEOUT)) {
        printf("Send domain control request data failed\n");
        close(sfd);
        return -1;
    }

    printf("receiving reply...\n");
    LyRespond respond;
    while (1) {
        if (ly_recv(sfd, &respond, sizeof(LyRespond), 0, RECV_TIMEOUT)) {
            printf("Get domain control respond error.\n");
            close(sfd);
            return -1;
        }

        break;
    }

    close(sfd);
    if (respond.status != 0) {
        printf("start job failed, respond status is %d\n", respond.status);
    }
    else {
        printf("start job succeeds\n");
    }

    return 0;
}

int stop_test_domain()
{
    return 0;
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
    struct epoll_event events[MAX_EVENTS];
    while (ret != -1) {
        if (g_state == 0) {
            if (mcast_send_join(1369) != 0) {
                printf("mcast_send_join error\n");
                break;
            }
        }
        else if (g_state == 2) {
            /* sleep for a while to allow lynode work socket starts */
            sleep(2);
            if (start_test_domain() != 0) {
                printf("start_test_domain error\n");
                break;
            }
            g_state = 3;
        }
        else if (g_state == 3) {
            if (stop_test_domain() != 0) {
                printf("stop_test_domain error\n");
                break;
            }
            g_state = 4;
        }
        else if (g_state == 4) {
            printf("test passed\n");
            break;
        }

        n = epoll_wait(g_efd, events, MAX_EVENTS, -1);
        for (i = 0; i < n; i++) {
            if (events[i].events & EPOLLIN && events[i].data.fd == g_efd) {
                printf("g_efd has data in. ???\n");
                ret = -1;
                break;
            }
            else if (events[i].events & EPOLLIN &&
                     events[i].data.fd == g_wfd) {
                printf("g_wfd has data in.\n");
                if (epoll_work_recv() != 0) {
                    printf("epoll_work_recv error\n");
                    ret = -1;
                    break;
                }
            }
            else if (events[i].events & EPOLLIN &&
                     events[i].data.fd == g_kfd) {
                printf("g_kfd has data in. ???\n");
                if (epoll_keepalive_recv() != 0) {
                    printf("epoll_work_recv error\n");
                    ret = -1;
                    break;
                }
            }
            else if (events[i].events & EPOLLRDHUP &&
                     events[i].data.fd == g_efd) {
                printf("g_efd got hup. ???\n");
                ret = -1;
                break;
            }
            else if (events[i].events & EPOLLRDHUP &&
                     events[i].data.fd == g_wfd) {
                printf("g_wfd got hup. ???\n");
                ret = -1;
                break;
            }
            else if (events[i].events & EPOLLRDHUP &&
                     events[i].data.fd == g_kfd) {
                printf("g_kfd got hup. exit\n");
                ret = 1;
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
    if (g_kfd != -1)
        close(g_kfd);
    return 0;
}
