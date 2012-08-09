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
#include <time.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "../util/lyxml.h"
#include "postgres.h"
#include "entity.h"
#include "lyclc.h"
#include "lyjob.h"

static time_t g_job_time_query_node = 0;
static time_t g_job_time_cleanup_node = 0;
static time_t g_job_time_query_instance = 0;

int job_internal_query_instance(int id)
{
    if (id <= 0)
        return -1;

    int node_id = db_instance_get_node(id);
    if (node_id <= 0)
        return -1;

    int ent_id = ly_entity_find_by_db(LY_ENTITY_NODE, node_id);
    if (ent_id < 0 || !ly_entity_is_registered(ent_id))
        return -1;

    int fd = ly_entity_fd(ent_id);
    if (fd < 0)
        return -1;

    char ins_domain[21];
    if (g_c->vm_name_prefix == NULL)
        snprintf(ins_domain, 20, "i-%d", id);
    else
        snprintf(ins_domain, 20, "%s%d", g_c->vm_name_prefix, id);

    NodeCtrlInstance ii;
    ii.req_id = 0;
    ii.req_action = LY_A_NODE_QUERY_INSTANCE;
    ii.ins_id = id;
    ii.ins_domain = ins_domain;
    char * xml = lyxml_data_instance_other(&ii, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    logdebug(_("sending query request to instance %d\n"), id);
    int len = strlen(xml);
    if (ly_packet_send(fd, PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST, xml, len) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        free(xml);
        return -1;
    }

    free(xml);
    return 0;
}

static void  __query_instance_all(void)
{
    /* logdebug(_("%s is called\n"), __func__); */

    int ins_num = 0;
    int * ins_id = db_instance_get_all(&ins_num);;
    if (ins_num <= 0 || ins_id == NULL)
        return;
    for (int i = 0; i < ins_num; i++) {
        job_internal_query_instance(ins_id[i]);
    }
    free(ins_id);
    return;
}

static int __query_node(int ent_id)
{
    if (ent_id < 0 || !ly_entity_is_registered(ent_id))
        return -1;

    int fd = ly_entity_fd(ent_id);
    if (fd < 0)
        return -1;

    char * xml = lyxml_data_node_info(0, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    logdebug(_("sending node query to entity %d...\n"), ent_id);
    int len = strlen(xml);
    if (ly_packet_send(fd, PKT_TYPE_CLC_NODE_CONTROL_REQUEST, xml, len) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        free(xml);
        return -1;
    }

    free(xml);
    return 0;
}

static void  __query_node_all(void)
{
    /* logdebug(_("%s is called\n"), __func__); */

    int ent_curr = -1;
    while(1) {
        NodeInfo * ni = ly_entity_data_next(LY_ENTITY_NODE, &ent_curr);
        if (ni == NULL)
            break;
        logdebug(_("query entity %d, node %d\n"), ent_curr, ni->host_tag);
        __query_node(ent_curr);
    }
    return;
}

static int __cleanup_node(int ent_id)
{
    return 0;
}

static void __cleanup_node_all(void)
{
    /* logdebug(_("%s is called\n"), __func__); */

    int ent_curr = -1;
    while(1) {
        NodeInfo * ni = ly_entity_data_next(LY_ENTITY_NODE, &ent_curr);
        if (ni == NULL)
            break;
        logdebug(_("cleanup entity %d, node %d\n"), ent_curr, ni->host_tag);
        __cleanup_node(ent_curr);
    }
    return;
}

int job_internal_dispatch(void)
{
    time_t now;
    time(&now);

    if (now - g_job_time_query_node > CLC_JOB_QUERY_NODE_INTERVAL) {
        __query_node_all();
        g_job_time_query_node = now;
    }
    else if (now < g_job_time_query_node)
        g_job_time_query_node = now;

    if (now - g_job_time_cleanup_node > CLC_JOB_CLEANUP_NODE_INTERVAL) {
        __cleanup_node_all();
        g_job_time_cleanup_node = now;
    }
    else if (now < g_job_time_cleanup_node)
        g_job_time_cleanup_node = now;

    if (now - g_job_time_query_instance > CLC_JOB_QUERY_INSTANCE_INTERVAL) {
        __query_instance_all();
        g_job_time_query_instance = now;
    }
    else if (now < g_job_time_query_instance)
        g_job_time_query_instance = now;

    return 0;
}

int job_internal_init(void)
{
    time(&g_job_time_cleanup_node);
    g_job_time_query_node = g_job_time_cleanup_node -
                            CLC_JOB_QUERY_NODE_INTERVAL;
    g_job_time_query_instance = g_job_time_cleanup_node -
                                CLC_JOB_QUERY_INSTANCE_INTERVAL;

    return 0;
}
