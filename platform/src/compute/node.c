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
#include <stdarg.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "../util/lypacket.h"
#include "../util/lyutil.h"
#include "../util/lyxml.h"
#include "domain.h"
#include "handler.h"
#include "node.h"


/*
** function to send out node report
**
** the function will be used as logging callback,
** no any logging function is allowed here
*/
void ly_node_send_report(int type, char * msg)
{
    if (g_c == NULL || g_c->node == NULL)
        return;

    if (type >= LYERROR)
        g_c->node->status = NODE_STATUS_ERROR;
    else if (type == LYWARN && g_c->node->status != NODE_STATUS_ERROR)
        g_c->node->status = NODE_STATUS_CHECK;

    if (g_c->wfd < 0) {
        return;
    }

    LYReport r;
    r.from = LY_ENTITY_NODE;
    r.to = LY_ENTITY_CLC;
    r.status = g_c->node->status;
    r.msg = msg;
    char * xml = lyxml_data_report(&r, NULL, 0);
    if (xml == NULL)
        return;
    ly_packet_send(g_c->wfd, PKT_TYPE_NODE_REPORT, xml, strlen(xml));
    free(xml);
    return;
}

void ly_node_send_report_resource(void)
{
    if (g_c == NULL || g_c->node == NULL)
        return;

    if (g_c->wfd < 0)
        return;

    LYReport r;
    r.from = LY_ENTITY_NODE;
    r.to = LY_ENTITY_CLC;
    if (ly_node_info_update() < 0)
        r.status = LY_S_FINISHED_FAILURE;
    else
        r.status = LY_S_FINISHED_SUCCESS;
    r.msg = NULL;
    r.data = g_c->node;
    logdebug(_("sending node info report...\n"));
    char * xml = lyxml_data_report_node_info(&r, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return;
    }
    ly_packet_send(g_c->wfd, PKT_TYPE_NODE_REPORT, xml, strlen(xml));
    free(xml);
    return;
}
                            
int ly_node_busy(void)
{
    int load = lyutil_load_average(LOAD_AVERAGE_LAST_1M);
    return load > LY_NODE_LOAD_MAX ? 1 : 0;
}

int ly_node_info_update()
{
    if (g_c == NULL || g_c->node == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -255;
    }

    NodeInfo * nf = g_c->node;
    if (g_c->node_ip != NULL) {
        if (nf->host_ip == NULL || strcmp(g_c->node_ip, nf->host_ip) != 0) {
            if (nf->host_ip)
                free(nf->host_ip);
            nf->host_ip = strdup(g_c->node_ip);
        }
    }

    nf->mem_free = lyutil_free_memory();
    if (nf->mem_free == 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    nf->storage_free = lyutil_free_storage(g_c->config.ins_data_dir);
    if (nf->storage_free == 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int load_average = lyutil_load_average(LOAD_AVERAGE_LAST_1M);
    if (load_average < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    nf->load_average = load_average;

    nf->status = g_c->state;

    if (nf->status >= NODE_STATUS_ONLINE &&
        nf->status != NODE_STATUS_ERROR &&
        nf->status != NODE_STATUS_CHECK) {
        if (load_average > LY_NODE_LOAD_MAX || ly_handler_busy()) {
            nf->status = NODE_STATUS_BUSY;
            logdebug(_("node busy %d %d\n"), load_average, LY_NODE_LOAD_MAX);
        }
        else
            nf->status = NODE_STATUS_READY;
    }

    if (libvirt_node_info_update(nf) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return 0;
}

NodeInfo * ly_node_info_init(void)
{
    if (g_c == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return NULL;
    }

    NodeInfo * nf = malloc(sizeof(NodeInfo));
    if (nf == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return NULL;
    }

    bzero(nf, sizeof(NodeInfo));
    nf->status = NODE_STATUS_UNKNOWN;
    nf->cpu_arch = CPU_ARCH_UNKNOWN;
    nf->hypervisor = HYPERVISOR_IS_UNKNOWN;
    nf->host_tag = -1;

    int ret;
    ret = libvirt_hypervisor();
    if (ret < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }
    nf->hypervisor = ret;

    ret = libvirt_node_info(nf);
    if (ret < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    nf->host_name = libvirt_hostname();
    if (nf->host_name == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    nf->mem_free = lyutil_free_memory();
    if (nf->mem_free == 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    nf->storage_free = lyutil_free_storage(g_c->config.ins_data_dir);
    if (nf->storage_free == 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    nf->storage_total = lyutil_total_storage(g_c->config.ins_data_dir);
    if (nf->storage_free == 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    int load_average = lyutil_load_average(LOAD_AVERAGE_LAST_15M);
    if (load_average < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }
    nf->load_average = load_average;

    return nf;

failed:
    luoyun_node_info_cleanup(nf);
    return NULL;
}
