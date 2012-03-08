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
#include <unistd.h>
#include <stddef.h>
#include <sys/types.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "../util/lypacket.h"
#include "../util/lyutil.h"
#include "../util/lyauth.h"
#include "lyclc.h"
#include "node.h"
#include "entity.h"

#define LY_ENTITY_MAX            1024

static int g_entity_clc = 0;
static LYEntity *g_entity_store = NULL;
static LIST_HEAD(g_node_list);
static LIST_HEAD(g_instance_list);

/*
** entity storage handlers
** 
** NOT thread safe
*/

/* init entity store */
int ly_entity_store_init(void)
{
    if (g_entity_store != NULL)
        return -255;

    int size = LY_ENTITY_MAX;

    g_entity_store = malloc(size * sizeof(LYEntity));
    if (g_entity_store == NULL)
        return -1;
    bzero(g_entity_store, size * sizeof(LYEntity));

    int i;
    for (i = 0; i < size; i++) {
        (g_entity_store + i)->id = -1;
        (g_entity_store + i)->fd = -1;
        (g_entity_store + i)->db_id = -1;
    }

    INIT_LIST_HEAD(&g_node_list);
    INIT_LIST_HEAD(&g_instance_list);
    return 0;
}

/* get a new entity object */
int ly_entity_new(int fd)
{
    LYEntity *ent = g_entity_store;
    if (ent == NULL || fd < 0)
        return -255;

    int i;
    for (i = 0; i < LY_ENTITY_MAX; i++, ent++) {
        if (ent->id == -1)
            break;
    }

    if (i == LY_ENTITY_MAX)
        return -1;

    /* entity must be cleaned and freed already*/
    if (ent->entity || ent->auth.challenge || ent->auth.secret)
        return -1;

    if (ent->pkt == NULL) {
        ent->pkt = malloc(sizeof(LYPacketRecv));
        if (ent->pkt == NULL)
            return -1;
        ent->pkt->pkt_buf = NULL;
        if (ly_packet_init(ent->pkt) < 0) {
            free(ent->pkt);
            ent->pkt = NULL;
            return -1;
        }
    }
    else 
        ly_packet_reinit(ent->pkt);


    INIT_LIST_HEAD(&ent->list);
    ent->db_id = -1;
    ent->type = LY_ENTITY_UNKNOWN;
    ent->flag = 0;
    ent->fd = fd;
    ent->id = (unsigned short)i;
    return i;
}

int ly_entity_init(int id, unsigned char type)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return -1;
    LYEntity *ent = g_entity_store + id;

    if (ent->type != LY_ENTITY_UNKNOWN)
        return 0; /* do nothing if set already */

    ent->type = type;
    if (type == LY_ENTITY_NODE) {
        ent->entity = malloc(sizeof(NodeInfo));
        if (ent->entity == NULL)
            return -1;
        bzero(ent->entity, sizeof(NodeInfo));
        list_add(&(ent->list), &(g_node_list));
    }
    else if (type == LY_ENTITY_OSM) {
        ent->entity = malloc(sizeof(OSMInfo));
        if (ent->entity == NULL)
            return -1;
        bzero(ent->entity, sizeof(OSMInfo));
        list_add(&(ent->list), &(g_instance_list));
    }
    else if (type == LY_ENTITY_CLC)
        g_entity_clc = id;

    return 0;
}

int ly_entity_fd(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return -1;
    return (g_entity_store + id)->fd;
}

int ly_entity_type(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return -1;
    return (g_entity_store + id)->type;
}

int ly_entity_db_id(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return -1;
    return (g_entity_store + id)->db_id;
}

LYPacketRecv *ly_entity_pkt(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return NULL;
    return (g_entity_store + id)->pkt;
}

void *ly_entity_data(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return NULL;
    return (g_entity_store + id)->entity;
}

AuthConfig *ly_entity_auth(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return NULL;
    return &(g_entity_store + id)->auth;
}

void *ly_entity_data_next(unsigned char ent_type, int * id)
{
    struct list_head * head;
    if (ent_type == LY_ENTITY_NODE)
        head = &g_node_list;
    else if (ent_type == LY_ENTITY_OSM)
        head = &g_instance_list;
    else
        return NULL;

    if (list_empty(head))
        return NULL;

    LYEntity * ent;
    if (id == NULL || *id <= 0 || *id >= LY_ENTITY_MAX)
        ent = list_entry(head->next, LYEntity, list);
    else {
        ent = g_entity_store + *id;
        if (list_is_last(&ent->list, head))
            return NULL;
        ent = list_entry(ent->list.next, LYEntity, list);       
    }

    *id = ent->id;
    return ent->entity;
}

int ly_entity_is_online(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return 0;
    return ((g_entity_store + id)->flag & LY_ENTITY_FLAG_STATUS_MASK) >=
            LY_ENTITY_FLAG_STATUS_ONLINE ? 1 : 0;
}

int ly_entity_is_authenticated(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return 0;
    return ((g_entity_store + id)->flag & LY_ENTITY_FLAG_STATUS_MASK) >=
            LY_ENTITY_FLAG_STATUS_AUTHENTICATED ? 1 : 0;
}

int ly_entity_is_registered(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return 0;
    return ((g_entity_store + id)->flag & LY_ENTITY_FLAG_STATUS_MASK) >=
            LY_ENTITY_FLAG_STATUS_REGISTERED ? 1 : 0;
}

int ly_entity_is_serving(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return 0;
    return ((g_entity_store + id)->flag & LY_ENTITY_FLAG_STATUS_MASK) >=
            LY_ENTITY_FLAG_STATUS_SERVING ? 1 : 0;
}

int ly_entity_is_enabled(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return 0;
    return ((g_entity_store + id)->flag & LY_ENTITY_FLAG_NODE_ENABLED) ? 1 : 0;
}

int ly_entity_update(int id, int db_id, int status)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return -1;
    if (status >= 0) {
        (g_entity_store + id)->flag &= ~LY_ENTITY_FLAG_STATUS_MASK;
        (g_entity_store + id)->flag |= status & LY_ENTITY_FLAG_STATUS_MASK;
    }
    if (status >= 0)
        (g_entity_store + id)->db_id = db_id;

    return 0;
}

int ly_entity_enable(int id, int db_id, int enble)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return -1;

    if (enble)
        (g_entity_store + id)->flag |= LY_ENTITY_FLAG_NODE_ENABLED;
    else 
        (g_entity_store + id)->flag &= ~LY_ENTITY_FLAG_NODE_ENABLED;

    if (db_id >= 0)
        (g_entity_store + id)->db_id = db_id;

    return 0;
}

int ly_entity_find_by_db(int ent_type, int db_id)
{
    struct list_head * head;
    if (ent_type == LY_ENTITY_NODE)
        head = &g_node_list;
    else if (ent_type == LY_ENTITY_OSM)
        head = &g_instance_list;
    else 
        return -1;

    LYEntity * curr;
    list_for_each_entry(curr, head, list) {
        if (curr->db_id == db_id)
            return curr->id;
    }
    return -1;
}

int ly_entity_node_active(char * ip)
{
    LYEntity * curr;
    list_for_each_entry(curr, &g_node_list, list) {
        NodeInfo * nf = curr->entity;
        if (ly_entity_is_registered(curr->id) &&
            nf->ip && strcmp(nf->ip, ip) == 0)
            return 1;
    }
    return 0;
}

int ly_entity_clc(void)
{
    return g_entity_clc;
}

int ly_entity_release(int id)
{
    if (g_entity_store == NULL || id < 0 || id >= LY_ENTITY_MAX)
        return -1;
    LYEntity *ent = g_entity_store + id;
    list_del(&ent->list);

    if (ent->fd >= 0)
        close(ent->fd);
    ent->fd = -1;
    ent->id = -1;
    ent->db_id = -1;
    ent->type = LY_ENTITY_UNKNOWN;
    ent->flag = 0;

    /* don't free packet buffer
    if (ent->pkt) {
        ly_packet_cleanup(ent->pkt);
        free(ent->pkt);
        ent->pkt = NULL;
    }
    */
    if (ent->entity) {
        if (ent->type == LY_ENTITY_NODE)
            luoyun_node_info_cleanup(ent->entity);
        else if (ent->type == LY_ENTITY_OSM)
            luoyun_osm_info_cleanup(ent->entity);
        free(ent->entity);
        ent->entity = NULL;
    }

    lyauth_free(&ent->auth);

    return 0;
}

void ly_entity_store_destroy(void)
{
    if (g_entity_store == NULL)
        return;
    LYEntity *ent = g_entity_store;
    int i;
    for (i = 0; i < LY_ENTITY_MAX; i++, ent++) {
        if (ent->fd >= 0)
            close(ent->fd);
        if (ent->pkt){
            ly_packet_cleanup(ent->pkt);
            free(ent->pkt);
        }
        if (ent->entity) {
            if (ent->type == LY_ENTITY_NODE)
                luoyun_node_info_cleanup(ent->entity);
            else if (ent->type == LY_ENTITY_OSM)
                luoyun_osm_info_cleanup(ent->entity);
            free(ent->entity);
        }
        lyauth_free(&ent->auth);
    }
    free(g_entity_store);
    g_entity_store = NULL;
    return;
}

void ly_entity_print_node()
{
    LYEntity * curr;
    list_for_each_entry(curr, &(g_node_list), list) {
        logsimple("node id %d, db_id %d\n", curr->id, curr->db_id);
        if (curr->entity)
           luoyun_node_info_print(curr->entity);
    }
}

void ly_entity_print_osm()
{
    LYEntity * curr;
    list_for_each_entry(curr, &(g_instance_list), list) {
        logsimple("osm id %d, db_id %d\n", curr->id, curr->db_id);
        if (curr->entity)
           luoyun_osm_info_print(curr->entity);
    }
}

