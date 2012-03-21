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

#define THIS_IP "192.168.1.107"

int g_efd = -1;
int g_wfd = -1;
int g_nfd = -1;
LYPacketRecv g_nfd_pkt;

int g_state = 0;

static void __print_recv_buf(char *buf)
{
    printf("%02x, %02x, %02x, %02x, %02x\n",
              buf[0], buf[1], buf[2], buf[3], (unsigned)buf[4]);
    char l[5];
    l[0] = buf[1];
    l[1] = buf[2];
    l[2] = buf[3];
    l[3] = buf[4];
    l[4] = 0;
    int len = atoi(l);
    if (len > 0 && len < 2000)
       printf("%s\n", &buf[5]);
}

void print_node_info(NodeInfo * N)
{
    printf("node = {\n"
           "\tstatus = %d\n"
           "\thostname = %s\n"
           "\tip = %s\n"
           "\tarch = %d\n"
           "\thypervisor = %d\n"
           "\tmax_memory = %d\n"
           "\tmax_cpus = %d\n"
           "\tcpu_model = %s\n"
           "\tcpu_mhz = %d\n"
           "\tload_average = %d\n" "\tfree_memory = %d\n"
           /*"\tcreated = %d\n" */
           /*"\tupdated = %d\n" */
           "}\n",
           N->status, N->host_name, N->host_ip,
           N->cpu_arch, N->hypervisor,
           N->mem_max, N->cpu_max, N->cpu_model,
           N->cpu_mhz, N->load_average, N->mem_free);
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
    sprintf(databuf1, "join %s %d", THIS_IP, port);
    int datalen = strlen(databuf1);

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
    localInterface.s_addr = inet_addr(THIS_IP);
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
    char databuf[400];
    *(int *)databuf = PKT_TYPE_JOIN_REQUEST;
    *((int *)databuf + 1) = datalen;
    sprintf(databuf + 8, "%s", databuf1);
    sendto(sd, databuf, datalen+8, 0, (struct sockaddr *) &groupSock, sizeof(groupSock));
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
    printf("%d received\n%d %d %s\n", ret, 
                         *(unsigned int*)request, 
                         *(unsigned int*)&request[1],
                         request + 8);

    char * idstr = xml_xpath_prop_from_str(request + 8, "/luoyun/request", "id");
    if (idstr)
        printf("id = %s\n", idstr);
    else {
        printf("can't get idstr\n");
        return -1;
    }

    printf("sending reply\n");
#if 0
    char * reply = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>"
                     "<luoyun>"
                       "<from entity=\"clc\"/>"
                       "<to entity=\"node\"/>"
                       "<response id=\"%s\">"
                           "<result>sucess</result>"
                       "</response>"
                     "</luoyun>";
    char response[400];
    sprintf(response, reply, idstr);
    ly_packet_send(infd, 1, response, strlen(response));
#else
    LYReply r;
    r.req_id = atoi(idstr);
    r.from = LY_ENTITY_NODE;
    r.to = LY_ENTITY_CLC;
    r.status = LY_S_REGISTERING_DONE_SUCCESS;
    r.msg = "success";
    char * response = lyxml_data_reply(&r, NULL, 0);
    ly_packet_send(infd, PKT_TYPE_NODE_REGISTER_REPLY, response, strlen(response));
    free(response);
#endif    

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
    ev.events = EPOLLIN | EPOLLET;
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

static int __query_test_node()
{
   if (g_nfd < 0)
       return -1;

    char * xml = lyxml_data_node_info(lyclc_new_request_id(), NULL, 0);
    if (xml == NULL) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }

    printf("sending node query ...\n");
    int len = strlen(xml);
    if (ly_packet_send(g_nfd, PKT_TYPE_CLC_NODE_CONTROL_REQUEST, xml, len) < 0) {
        printf("error in %s(%d).\n", __func__, __LINE__);
        free(xml);
        return -1;
    }

    free(xml);
    return 0;
}

static int __query_test_domain()
{
   if (g_nfd < 0)
       return -1;

    NodeCtrlInstance ii;
    ii.req_id = lyclc_new_request_id();
    ii.req_action = LY_A_NODE_QUERY_INSTANCE;
    ii.ins_id = 1;
    ii.ins_name = "dongwu";
    char * xml = lyxml_data_instance_other(&ii, NULL, 0);
    if (xml == NULL) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }

    printf("sending query request ...\n");
    int len = strlen(xml);
    if (ly_packet_send(g_nfd, PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST, xml, len) < 0) {
        printf("error in %s(%d).\n", __func__, __LINE__);
        free(xml);
        return -1;
    }

    free(xml);
    return 0;
}

static int __process_work_xml(char *xml)
{
    printf("%s\n", xml);
    char * str;
   
    /* check for report */ 
    str = xml_xpath_text_from_str(xml, "/luoyun/report/status");
    if (str != NULL) {
        printf("report status %s\n", str);
        free(str);
        str = xml_xpath_text_from_str(xml, "/luoyun/report/message");
        printf("report status %s\n", str);
        free(str);
        return 0;
    }

    /* check for response */
    int status;
    str = xml_xpath_prop_from_str(xml, "/luoyun/response", "status");
    if (str != NULL) {
        status = atoi(str);
        free(str);
    }
    int id = 0;
    str = xml_xpath_prop_from_str(xml, "/luoyun/response", "id");
    if (str != NULL) {
        id = atoi(str);
        free(str);
    }
    str = xml_xpath_text_from_str(xml, "/luoyun/response/result");
    if (str != NULL) {
        printf("response for control request %d, status %d, %s\n", id, status, str);
        free(str);
    }
    else
        printf("response for control request %d, status %d\n", id, status);

    /* don't continue if request is not completed */
    if (!JOB_IS_FINISHED(status))
        return 0;

    /* check for node query */
    str = xml_xpath_text_from_str(xml, "/luoyun/response/data/memory/free");
    if (str != NULL) {
        char * s1 = xml_xpath_text_from_str(xml, "/luoyun/response/data/status");
        char * s2 = xml_xpath_text_from_str(xml, "/luoyun/response/data/load/average");
        printf("response for node query %d, status %d, %s %s %s\n", id, status, s1, str, s2);
        free(str);
        if (s1) free(s1);
        if (s2) free(s2);
        return 0;
    }

    /* instance control/query responses */
    str = xml_xpath_text_from_str(xml, "/luoyun/response/data/status");
    if (str != NULL) {
        printf("response for query request, status %s\n", str);
        free(str);
        if (g_state == 3)
            g_state = 4;
        if (g_state == 5)
            g_state = 6;
        if (g_state == 7)
            g_state = 8;
    }
    else {
        __query_test_domain();
        __query_test_node();
    }

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
        else if (PKT_TYPE_ENTITY_GROUP_NODE(ly_packet_type(pkt)) ||
                 PKT_TYPE_ENTITY_GROUP_CLC(ly_packet_type(pkt))) {
            ret = __process_work_xml(ly_packet_data(pkt, NULL));
            if (ret < 0)
                printf("xml packet process error in %s.\n", __func__);
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

int start_test_domain()
{
   if (g_nfd < 0)
       return -1;

    NodeCtrlInstance ii;
    bzero(&ii, sizeof(NodeCtrlInstance));
    ii.req_id = lyclc_new_request_id();
    ii.req_action = LY_A_NODE_RUN_INSTANCE;
    ii.ins_id = 1;
    ii.ins_status = DOMAIN_S_NEW;
    ii.ins_name = "dongwu";
    //ii.ins_vcpu = 1;
    //ii.ins_mem = 256000;
    ii.ins_mac = "aa:bb:cc:dd:ee:ff";
    //ii.ins_ip = "";
    ii.app_id = 2;
    ii.app_name = "ubantu";
    //ii.app_uri = "http://localhost:8080/luoyun/1/os.gz";
    ii.app_checksum = "589595fc7bfe16196afdaaa3a1795a3b";
    //ii.osm_clcip = THIS_IP;
    //ii.osm_clcport = 1369;
    ii.osm_clcip = "";
    ii.osm_clcport = 0;
    char * xml = lyxml_data_instance_run(&ii, NULL, 0);
    if (xml == NULL) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }

    printf("sending request ...\n");
    int len = strlen(xml);
    if (ly_packet_send(g_nfd, PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST, xml, len) < 0) {
        printf("error in %s(%d).\n", __func__, __LINE__);
        free(xml);
        return -1;
    }

    free(xml);
    return 0;
}

int stop_test_domain()
{
   if (g_nfd < 0)
       return -1;

    NodeCtrlInstance ii;
    ii.req_id = lyclc_new_request_id();
    ii.req_action = LY_A_NODE_STOP_INSTANCE;
    ii.ins_id = 1;
    ii.ins_name = "dongwu";
    char * xml = lyxml_data_instance_stop(&ii, NULL, 0);
    if (xml == NULL) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }

    printf("sending stop request ...\n");
    int len = strlen(xml);
    if (ly_packet_send(g_nfd, PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST, xml, len) < 0) {
        printf("error in %s(%d).\n", __func__, __LINE__);
        free(xml);
        return -1;
    }

    free(xml);
    return 0;
}

int destroy_test_domain()
{
   if (g_nfd < 0)
       return -1;

    NodeCtrlInstance ii;
    ii.req_id = lyclc_new_request_id();
    ii.req_action = LY_A_NODE_DESTROY_INSTANCE;
    ii.ins_id = 1;
    ii.ins_name = "dongwu";
    char * xml = lyxml_data_instance_other(&ii, NULL, 0);
    if (xml == NULL) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }

    printf("sending destroy request ...\n");
    int len = strlen(xml);
    if (ly_packet_send(g_nfd, PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST, xml, len) < 0) {
        printf("error in %s(%d).\n", __func__, __LINE__);
        free(xml);
        return -1;
    }

    free(xml);
    return 0;
}

int main(int argc, char **argv)
{
/*
    char * ptr = lyxml_data_join(1, "11.11.1.1", 22335, NULL, 0);
    printf(ptr);printf("\n%ld\n", strlen(ptr));
    free(ptr);
    NodeInfo ni = { 222222, 111111, 8, 2000, 1, 1450, 1, 1, 1, 1, 1,
                    "i686", "localhost", THIS_IP };
    ptr = lyxml_data_node_register(&ni, NULL, 0);
    printf(ptr);printf("\n%ld\n", strlen(ptr));
    free(ptr);
    NodeCtrlInstance ii = { 1, LA_DOMAIN_RUN, 2, 1, "wiki-ly", 1, 1024, "aa:bb:cc:dd:ee:ff",
                        "", 3, "wiki", "http://localhost:8080/root.tgz",
                        "", THIS_IP, 1450};
    ptr = lyxml_data_instance_run(&ii, NULL, 0);
    printf(ptr);printf("\n%ld\n", strlen(ptr));
    free(ptr);
    ii.req_action = LA_DOMAIN_STOP;
    ptr = lyxml_data_instance_stop(&ii, NULL, 0);
    printf(ptr);printf("\n%ld\n", strlen(ptr));
    free(ptr);
    ptr = lyxml_data_instance_register(3, "corei5", THIS_IP, NULL, 0);
    printf(ptr);printf("\n%ld\n", strlen(ptr));
    free(ptr);
    LYReply r = { LUOYUN_ENTITY_NODE, LUOYUN_ENTITY_CLC, 4,
                  LUOYUN_REPLY_STATUS_DONE, 0, "sucess" };
    ptr = lyxml_data_reply(&r, NULL, 0);
    printf(ptr);printf("\n%ld\n", strlen(ptr));
    free(ptr);
    return 0;
*/
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
            g_state = 1;
        }
        else if (g_state == 2) {
            /* sleep for a while to allow lynode work socket starts */
            printf("sleep 2 seconds before start test domain\n");
            sleep(2);
            if (start_test_domain() != 0) {
                printf("start_test_domain error\n");
                break;
            }
            /*
            printf("sleep 2 seconds before stop test domain\n");
            sleep(2);
            if (stop_test_domain() != 0) {
                printf("stop_test_domain error\n");
                break;
            }
            */
            g_state = 3;
        }
        else if (g_state == 4) {
            printf("sleep 2 seconds before stop test domain\n");
            sleep(2);
            if (stop_test_domain() != 0) {
                printf("stop_test_domain error\n");
                break;
            }
            g_state = 5;
        }
        else if (g_state == 6) {
            printf("sleep 3 seconds before destroy test domain\n");
            sleep(3);
            if (destroy_test_domain() != 0) {
                printf("destroy_test_domain error\n");
                break;
            }
            g_state = 7;
        }
        else if (g_state == 8) {
            printf("test passed\n");
            break;
        }

        n = epoll_wait(g_efd, events, MAX_EVENTS, 5000);
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
