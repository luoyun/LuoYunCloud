#ifndef __LY_INCLUDE_CLC_LYENTITY_H
#define __LY_INCLUDE_CLC_LYENTITY_H

#include "../util/list.h"
#include "../util/lyauth.h"
#include "../util/lypacket.h"

typedef struct LYEntity_t {
    /* socket file descriptor */
    int fd;
    /* authentication verification */
    AuthConfig auth;
    /* packet receive struct */
    LYPacketRecv *pkt;
    /* entity id */
    short id;
    /* entity type */
    unsigned char type;
    /* entity flag, interpretion depends on entity type */
    unsigned char flag;
    /* entity specific id in DB */
    int db_id;
    /* entity active list, doubly linked circular list */
    struct list_head list;
    /* entity specific data */
    void *entity;
} LYEntity;

#define LY_ENTITY_FLAG_STATUS_MASK 		0x07
#define LY_ENTITY_FLAG_STATUS_OFFLINE 		0x0
#define LY_ENTITY_FLAG_STATUS_ONLINE 		0x01
#define LY_ENTITY_FLAG_STATUS_AUTHENTICATED	0x02
#define LY_ENTITY_FLAG_STATUS_REGISTERED	0x03
#define LY_ENTITY_FLAG_STATUS_RUNNING		0x04
#define LY_ENTITY_FLAG_STATUS_SERVING		0x05
#define LY_ENTITY_FLAG_NODE_ENABLED	 	0x08

int ly_entity_store_init(void);
int ly_entity_new(int fd);
int ly_entity_init(int id, unsigned char type);
int ly_entity_fd(int id);
int ly_entity_type(int id);
int ly_entity_db_id(int id);
LYPacketRecv *ly_entity_pkt(int id);
void *ly_entity_data(int id);
void *ly_entity_data_next(unsigned char type, int * id);
AuthConfig *ly_entity_auth(int id);
int ly_entity_find_by_db(int ent_type, int db_id);
int ly_entity_is_online(int id);
int ly_entity_is_authenticated(int id);
int ly_entity_is_registered(int id);
int ly_entity_is_running(int id);
int ly_entity_is_serving(int id);
int ly_entity_is_enabled(int id);
int ly_entity_update(int id, int db_id, int status);
int ly_entity_enable(int id, int db_id, int enable);
int ly_entity_node_active(char * ip);
int ly_entity_clc(void);
int ly_entity_release(int id);
void ly_entity_store_destroy(void);
void ly_entity_print_node(void);
void ly_entity_print_osm(void);

#endif
