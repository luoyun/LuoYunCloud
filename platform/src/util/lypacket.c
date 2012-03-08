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

#include "lypacket.h"

#include "logging.h"
int ly_packet_send(int fd, int32_t type, void * data, int32_t size)
{
    if (fd < 0 || type <= 0 || data == NULL || size <= 0)
       return -255;

    if (size + sizeof(LYPacketHeader) >= LUOYUN_PACKET_SIZE_MAX)
       return -1;

    LYPacketHeader header;
    /* assume same endiness on all entities in system
    header.type = htonl(type);
    header.length = htonl(size);
    */
    header.type = type;
    header.length = size;

    struct iovec s[2];
    s[0].iov_base = &header;
    s[0].iov_len = sizeof(header);
    s[1].iov_base = data;
    s[1].iov_len = size;

    struct msghdr msg;
    msg.msg_name = NULL;
    msg.msg_namelen = 0;
    msg.msg_iov = s;
    msg.msg_iovlen = 2;
    msg.msg_control = NULL;
    msg.msg_controllen = 0;
    int datalen = sendmsg(fd, &msg, MSG_NOSIGNAL);
    if (datalen < size + sizeof(header))
        return -1;

    return 0;
}

/* size is the length of data just received */
int ly_packet_recv(LYPacketRecv * pkt, int size)
{
    if (pkt == NULL)
        return -1;

    if (size < 0)
        return 0;

    char *buf = (char *) pkt->pkt_buf;
    if (buf == NULL)
        return -1;
    pkt->pkt_buf_received += size;

    if (pkt->pkt_buf_received < sizeof(LYPacketHeader)) {
        return 0;
    }
    /* assume the endiness of sending and receiving entities are same */
    pkt->pkt_header = *(LYPacketHeader *)buf;

    int this_pkt_total = pkt->pkt_header.length + sizeof(LYPacketHeader);
    if (this_pkt_total <= pkt->pkt_buf_received) {
        pkt->pkt_data = buf + sizeof(LYPacketHeader);
        pkt->pkt_head_byte = *(buf + this_pkt_total);
        *(buf + this_pkt_total) = 0;
        return 1;
    }
    else
        return 0;
}

int ly_packet_recv_done(LYPacketRecv * pkt)
{
    if (pkt->pkt_buf_received < sizeof(LYPacketHeader)) {
        pkt->pkt_buf_received = 0;
        return 0;
    }

    int this_pkt_total = pkt->pkt_header.length + sizeof(LYPacketHeader);
    if (pkt->pkt_buf_received <= this_pkt_total) {
        pkt->pkt_buf_received = 0;
        return 0;
    }

    unsigned char *buf = (unsigned char *) pkt->pkt_buf;
    pkt->pkt_buf_received -= this_pkt_total;
    memmove(buf, buf + this_pkt_total, pkt->pkt_buf_received);
    *buf = pkt->pkt_head_byte;
    return 0;
}

void *ly_packet_buf(LYPacketRecv * pkt, int *size)
{
    if (pkt->pkt_buf == NULL)
        return NULL;

    if (pkt->pkt_buf_size <= pkt->pkt_buf_received){
        *size = 0;
        return NULL;
    }
    else
        *size = pkt->pkt_buf_size - pkt->pkt_buf_received;

    return (unsigned char *) pkt->pkt_buf + pkt->pkt_buf_received;
}

int ly_packet_type(LYPacketRecv * pkt)
{
    if (pkt->pkt_buf == NULL || pkt->pkt_buf_received < sizeof(LYPacketHeader))
        return PKT_TYPE_UNKNOW;

    return pkt->pkt_header.type;
}

void *ly_packet_data(LYPacketRecv * pkt, int *size)
{
    if (pkt->pkt_buf == NULL || pkt->pkt_buf_received < sizeof(LYPacketHeader))
        return NULL;

    if (size)
        *size = pkt->pkt_header.length;
    return (unsigned char *) pkt->pkt_buf + sizeof(LYPacketHeader);
}

int ly_packet_init(LYPacketRecv * pkt)
{
    if (pkt->pkt_buf != NULL)
        free(pkt->pkt_buf);
    bzero(pkt, sizeof(LYPacketRecv));

    pkt->pkt_buf_size = LUOYUN_PACKET_SIZE_MAX;
    pkt->pkt_buf = malloc(pkt->pkt_buf_size);
    if (pkt->pkt_buf == NULL)
        return -1;

    /* save space for making string */
    pkt->pkt_buf_size = LUOYUN_PACKET_SIZE_MAX - 1;
    return 0;
}

void ly_packet_cleanup(LYPacketRecv * pkt)
{
    if (pkt->pkt_buf != NULL)
        free(pkt->pkt_buf);
    bzero(pkt, sizeof(LYPacketRecv));
}
