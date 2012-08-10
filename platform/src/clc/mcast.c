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
#include <arpa/inet.h>
#include <net/if.h>
#include <ifaddrs.h>
#include <unistd.h>             /* gethostname */
#include <netdb.h>              /* struct hostent */
#include <errno.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "postgres.h"
#include "lyclc.h"

#define LY_CLC_IP_MAX 4
static int g_clc_ip_num = 0;
static char *g_clc_ip[LY_CLC_IP_MAX];

static int __mcast_send_join(char *clcip)
{
    struct in_addr localInterface;
    struct sockaddr_in groupSock;
    int sd, ret = -1;

    /* use string format */
    char databuf1[100];
    sprintf(databuf1, "join %s %d", clcip, g_c->clc_port);
    int datalen = strlen(databuf1);

    /* build packet with header */
    char  databuf[100 + sizeof(LYPacketHeader)];
    LYPacketHeader * header = (LYPacketHeader *)databuf;
    header->type = PKT_TYPE_JOIN_REQUEST;
    header->length = strlen(databuf1);
    strncpy(&databuf[sizeof(LYPacketHeader)], databuf1, datalen);
    datalen += sizeof(LYPacketHeader);

    /* Create a datagram socket on which to send. */
    sd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sd < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* Initialize the group sockaddr structure */
    memset((char *) &groupSock, 0, sizeof(groupSock));
    groupSock.sin_family = AF_INET;
    groupSock.sin_addr.s_addr = inet_addr(g_c->clc_mcast_ip);
    groupSock.sin_port = htons(g_c->clc_mcast_port);

    /* Set local interface for outbound multicast datagrams. */
    /* The IP address specified must be associated with a local, */
    /* multicast capable interface. */
    localInterface.s_addr = inet_addr(clcip);
    if (setsockopt
        (sd, IPPROTO_IP, IP_MULTICAST_IF, (char *) &localInterface,
         sizeof(localInterface)) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out;
    }

    /* Send a message to the multicast group specified by the */
    /* groupSock sockaddr structure. */
    if (sendto(sd, databuf, datalen, 0, (struct sockaddr *) &groupSock,
               sizeof(groupSock)) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out;
    }

    ret = 0;
out:
    close(sd);
    return ret;
}

#if 0
int __ucast_send_join(char *clcip, char *ins_ip)
{
    struct sockaddr_in sock;
    int sd, ret = -1;

    /* use string format */
    char databuf1[100];
    sprintf(databuf1, "join %s %d", clcip, g_c->clc_port);
    int datalen = strlen(databuf1);

    /* build packet with header */
    char  databuf[100 + sizeof(LYPacketHeader)];
    LYPacketHeader * header = (LYPacketHeader *)databuf;
    header->type = PKT_TYPE_JOIN_REQUEST;
    header->length = strlen(databuf1);
    strncpy(&databuf[sizeof(LYPacketHeader)], databuf1, datalen);
    datalen += sizeof(LYPacketHeader);

    /* Create a datagram socket on which to send. */
    sd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sd < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* Initialize the group sockaddr structure */
    memset((char *) &sock, 0, sizeof(sock));
    sock.sin_family = AF_INET;
    sock.sin_addr.s_addr = inet_addr(ins_ip);
    sock.sin_port = htons(g_c->clc_mcast_port);

    /* Send a message to the multicast group specified by the */
    /* groupSock sockaddr structure. */
    ret = sendto(sd, databuf, datalen, 0, (struct sockaddr *) &sock,
                 sizeof(sock));
    if (ret < 0)
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);

    close(sd);
    return ret;
}

int __ucast_send_join_all(char *clcip)
{
    char *ins_ip[100];
    int num = db_instance_find_ip_by_status(DOMAIN_S_START, ins_ip, 100);
    if (num > 100) {
        logwarn(_("unicast join: more than 100 instances not registered?\n"));
        num = 100;
    }
    for (int i=0; i < num; i++) {
        loginfo(_("send join message to instance %s\n"), ins_ip[i]);
        if (__ucast_send_join(g_clc_ip[i], ins_ip[i]) < 0)
            loginfo(_("error in %s(%d)\n"), __func__, __LINE__);
    }
    return 0;
}
#endif

int ly_mcast_send_join(void)
{
    if (g_c->clc_ip) {
        if (__mcast_send_join(g_c->clc_ip) < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        return 0;
    }

    for (int i = 0; i < g_clc_ip_num; i++) {
        /* logdebug(_("send mcast on address: %s\n"), g_clc_ip[i]); */
        if (__mcast_send_join(g_clc_ip[i]) < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
    }

    return 0;
}

int ly_clc_ip_get(void)
{
    int i;
    if (g_clc_ip_num == 0) {
        for (i = 0; i < LY_CLC_IP_MAX; i++) {
            if (g_clc_ip[i]) {
                free(g_clc_ip[i]);
                g_clc_ip[i] = NULL;
            }
        }
    }
    else
        return 0;

    /* go through all INET interface */
    struct ifaddrs *ifaddr, *ifa;
    if (getifaddrs(&ifaddr) == -1) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    int ret = -1;
    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        char host[NI_MAXHOST];
        if (ifa->ifa_addr == NULL || ifa->ifa_addr->sa_family != AF_INET)
            continue;
        /* get ip */
        int s = getnameinfo(ifa->ifa_addr, sizeof(struct sockaddr_in),
                            host, NI_MAXHOST, NULL, 0, NI_NUMERICHOST);
        if (s != 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto out;
        }
        /* check hwaddr is real */
        struct ifreq buf;
        bzero(&buf, sizeof(buf));
        s = socket(AF_INET, SOCK_DGRAM, 0);
        strcpy(buf.ifr_name, ifa->ifa_name);
        if (ioctl(s, SIOCGIFHWADDR, &buf)) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto out;
        }
        close(s);
        if (buf.ifr_hwaddr.sa_data[0] == 0 &&
            buf.ifr_hwaddr.sa_data[1] == 0 &&
            buf.ifr_hwaddr.sa_data[2] == 0 &&
            buf.ifr_hwaddr.sa_data[3] == 0 &&
            buf.ifr_hwaddr.sa_data[4] == 0 &&
            buf.ifr_hwaddr.sa_data[5] == 0)
            continue;
        if (g_clc_ip_num < LY_CLC_IP_MAX) {
            g_clc_ip[g_clc_ip_num] = strdup(host);
            loginfo(_("CLC will use ip %s\n"), g_clc_ip[g_clc_ip_num]);
            g_clc_ip_num++;
        }
    }

    if (g_clc_ip_num > 0)
        ret = 0;
out:
    freeifaddrs(ifaddr);
    return ret;
}

int ly_is_clc_ip(char * ip)
{
    if (ip == NULL)
        return 0;

    if (g_c->clc_ip && strcmp(g_c->clc_ip, ip) == 0)
        return 1;

    for (int i = 0; i < g_clc_ip_num; i++) {
        if (strcmp(g_clc_ip[i], ip) == 0)
            return 1;
    }

    return 0;
}

void ly_clc_ip_clean(void)
{
    int i;
    for (i = 0; i < g_clc_ip_num; i++) {
        if (g_clc_ip[i]) {
            free(g_clc_ip[i]);
            g_clc_ip[i] = NULL;
        }
    }
    return;
}

