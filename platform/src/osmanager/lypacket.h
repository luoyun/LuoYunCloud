#ifndef __LUOYUN_INCLUDE_OSMANAGER_LYPACKET_H
#define __LUOYUN_INCLUDE_OSMANAGER_LYPACKET_H

#include "../luoyun/luoyun.h"

/*
** Packets transmited between sockets in LuoYun system always have 
** packet header which identifies the packet type and data length.
*/

/* LuoYun packet receive structure */
#define LUOYUN_PACKET_SIZE_MAX 4096

typedef struct LYPacketRecv_t {
    /* packet header */
    LYPacketHeader pkt_header;
 
    /* complete packet buffer */
    unsigned int pkt_buf_size;
    unsigned int pkt_buf_received;
    void *pkt_buf;

    /* points to packet data */
    /* for now it should be (char *)buf + sizeof(LYPacketHeader) */
    void *pkt_data;

    /* to help make packet a string */
    unsigned char pkt_head_byte;

} LYPacketRecv;

/* size is the length of data just received */
int ly_packet_recv(LYPacketRecv * pkt, int size);
/* re-org data after some data is processed */
int ly_packet_recv_done(LYPacketRecv * pkt);

int ly_packet_init(LYPacketRecv * pkt);
int ly_packet_reinit(LYPacketRecv * pkt);
void ly_packet_cleanup(LYPacketRecv * pkt);
void *ly_packet_data(LYPacketRecv * pkt, int *size);
void *ly_packet_buf(LYPacketRecv * pkt, int *size);
int ly_packet_type(LYPacketRecv * pkt);

/* send message with header */
int ly_packet_send(int fd, int32_t type, void * msg, int32_t size);

#endif
