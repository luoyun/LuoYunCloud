/*
** Copyright (C) 2012 LuoYun Co. 
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
#include <stddef.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <netdb.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <sys/ioctl.h>

void testgetifaddrs(void)
{
    struct ifaddrs *ifaddr, *ifa;
    if (getifaddrs(&ifaddr) == -1) {
        perror("getifaddrs");
        return;
    }
    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        char host[NI_MAXHOST];
        if (ifa->ifa_addr == NULL)
            continue;
        int family = ifa->ifa_addr->sa_family;
        printf("%s address family: %d, flag 0x%x\n", ifa->ifa_name, family, ifa->ifa_flags);
        if (family == AF_INET || family == AF_INET6) {
            int s = getnameinfo(ifa->ifa_addr,
                                (family ==
                                 AF_INET) ? sizeof(struct sockaddr_in) :
                                sizeof(struct sockaddr_in6),
                                host, NI_MAXHOST, NULL, 0, NI_NUMERICHOST);
            if (s != 0) {
                perror("getnameinfo");
                return;
            }
            printf("address: %s\n", host);
            struct ifreq buf;
            bzero(&buf, sizeof(buf));
            s = socket(AF_INET, SOCK_DGRAM, 0);
            strcpy(buf.ifr_name, ifa->ifa_name);
            if (ioctl(s, SIOCGIFHWADDR, &buf)) {
                perror("ioctl");
            }
            close(s);
            if (buf.ifr_hwaddr.sa_data[0] == 0 && buf.ifr_hwaddr.sa_data[1] == 0 &&
                buf.ifr_hwaddr.sa_data[2] == 0 && buf.ifr_hwaddr.sa_data[3] == 0 &&
                buf.ifr_hwaddr.sa_data[4] == 0 && buf.ifr_hwaddr.sa_data[5] == 0)
                continue;

            for (s = 0; s < 6; s++)
                printf("%02x:", (unsigned char)buf.ifr_hwaddr.sa_data[s]);
            printf("\n");
        }
    }
    freeifaddrs(ifaddr);
    return;
}

void testgetaddrinfo(void)
{
    char *port = "12345";
    struct addrinfo hints;
    struct addrinfo *result, *rp;
    int s;

    memset(&hints, 0, sizeof(struct addrinfo));
    hints.ai_family = AF_UNSPEC;        /* Return IPv4 and IPv6 choices */
    hints.ai_socktype = SOCK_STREAM;    /* We want a TCP socket */
    hints.ai_flags = AI_PASSIVE;        /* All interfaces */

    s = getaddrinfo(NULL, port, &hints, &result);
    if (s != 0) {
        printf("getaddrinfo: %s\n", gai_strerror(s));
        return;
    }

    for (rp = result; rp != NULL; rp = rp->ai_next) {
        printf("%s %d %d %d\n",
               inet_ntoa(((struct sockaddr_in *) rp->ai_addr)->sin_addr),
               ntohs(((struct sockaddr_in *) rp->ai_addr)->sin_port),
               ((struct sockaddr_in *) rp->ai_addr)->sin_family,
               ((struct sockaddr_in *) rp->ai_addr)->sin_family ==
               AF_INET ? 1 : 0);
        int sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        /* Fix me: Enable address reuse, for DEBUG */
        int on = 1;
        setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on));
        if (sfd == -1)
            continue;

        s = bind(sfd, rp->ai_addr, rp->ai_addrlen);
        if (s == 0) {
            printf("succesfully bind\n");
        }
        else
            printf("bind failed\n");
        s = listen(sfd, 5);
        if (s == 0) {
            printf("succesfully start listening\n");
        }
        else
            printf("listen failed\n");

        printf("sleeping for 5 seconds\n");
        sleep(5);

        close(sfd);

    }

    freeaddrinfo(result);
    return;
}

int main()
{
    //testgetaddrinfo();
    testgetifaddrs();
    printf("This is test program for luoyun cloud program!\n");
    return (0);
}
