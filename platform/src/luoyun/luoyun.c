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

#include "luoyun.h"
#include "../util/logging.h"

void luoyun_node_ctrl_instance_print(NodeCtrlInstance * ci)
{
    logsimple("Node Ctrl Instance struct:\n"
              "req_id = %d\n"
              "req_action = %d\n"
              "ins_id = %d\n"
              "ins_status = %d\n"
              "ins_name = %s\n"
              "ins_vcpu = %d\n"
              "ins_mem = %d\n"
              "ins_mac = %s\n"
              "ins_ip = %s\n"
              "ins_domain = %s\n"
              "app_id = %d\n"
              "app_name = %s\n"
              "app_uri = %s\n"
              "app_checksum = %s\n"
              "storage_ip = %s\n"
              "storage_method = %d\n"
              "storage_parm = %s\n"
              "osm_clcip = %s\n"
              "osm_clcport = %d\n"
              "osm_tag = %d\n"
              "osm_secret = %s\n"
              "osm_json = %s\n",
              ci->req_id, ci->req_action,
              ci->ins_id, ci->ins_status, ci->ins_name, ci->ins_vcpu,
              ci->ins_mem, ci->ins_mac, ci->ins_ip, ci->ins_domain,
              ci->app_id, ci->app_name, ci->app_uri, ci->app_checksum, 
              ci->storage_ip, ci->storage_method, ci->storage_parm,
              ci->osm_clcip, ci->osm_clcport, ci->osm_tag,
              ci->osm_secret ? "Not Empty" : "Empty", ci->osm_json);
    if (ci->ins_ip == NULL)
        logsimple("instance ip is NULL\n");
}

void luoyun_node_ctrl_instance_cleanup(NodeCtrlInstance * ci)
{
    if (ci == NULL)
        return;
    if (ci->ins_name)
        free(ci->ins_name);
    if (ci->ins_mac)
        free(ci->ins_mac);
    if (ci->ins_ip)
        free(ci->ins_ip);
    if (ci->ins_domain)
        free(ci->ins_domain);
    if (ci->app_name)
        free(ci->app_name);
    if (ci->app_uri)
        free(ci->app_uri);
    if (ci->app_checksum)
        free(ci->app_checksum);
    if (ci->storage_ip)
        free(ci->storage_ip);
    if (ci->storage_parm)
        free(ci->storage_parm);
    if (ci->osm_clcip)
        free(ci->osm_clcip);
    if (ci->osm_secret)
        free(ci->osm_secret);
    if (ci->osm_json)
        free(ci->osm_json);
    bzero(ci, sizeof(NodeCtrlInstance));
    return;
}

NodeCtrlInstance * luoyun_node_ctrl_instance_copy(NodeCtrlInstance * ci)
{
    if (ci == NULL)
        return NULL;

    NodeCtrlInstance *ret = malloc(sizeof(NodeCtrlInstance));
    if (ret == NULL)
        return NULL;
    *ret = *ci;
    if (ci->ins_name)
        ret->ins_name = strdup(ci->ins_name);
    if (ci->ins_mac)
        ret->ins_mac = strdup(ci->ins_mac);
    if (ci->ins_ip)
        ret->ins_ip = strdup(ci->ins_ip);
    if (ci->ins_domain)
        ret->ins_domain = strdup(ci->ins_domain);
    if (ci->app_name)
        ret->app_name = strdup(ci->app_name);
    if (ci->app_uri)
        ret->app_uri = strdup(ci->app_uri);
    if (ci->app_checksum)
        ret->app_checksum = strdup(ci->app_checksum);
    if (ci->osm_clcip)
        ret->osm_clcip = strdup(ci->osm_clcip);
    if (ci->storage_ip)
        ret->storage_ip = strdup(ci->storage_ip);
    if (ci->storage_parm)
        ret->storage_parm = strdup(ci->storage_parm);
    if (ci->osm_secret)
        ret->osm_secret = strdup(ci->osm_secret);
    if (ci->osm_json)
        ret->osm_json = strdup(ci->osm_json);
    return ret;
}

void luoyun_node_info_print(NodeInfo * nf)
{
    logsimple("Node Info = {\n"
              "\tstatus = %d\n"
              "\thypervisor = %d\n"
              "\thost_name = %s\n"
              "\thost_ip = %s\n"
              "\thost_tag = %d\n"
              "\tmem_max = %d\n"
              "\tmem_free = %d\n"
              "\tmem_commit = %d\n"
              "\tcpu_arch = %d\n"
              "\tcpu_max = %d\n"
              "\tcpu_model = %s\n"
              "\tcpu_mhz = %d\n"
              "\tcpu_commit = %d\n"
              "\tload_average = %d\n"
              "\tstorage_total = %d\n"
              "\tstorage_free = %d\n"
              "}\n",
              nf->status, nf->hypervisor, 
              nf->host_name, nf->host_ip, nf->host_tag,
              nf->mem_max, nf->mem_free, nf->mem_commit,
              nf->cpu_arch, nf->cpu_max, nf->cpu_model,
              nf->cpu_mhz, nf->cpu_commit,
              nf->load_average, nf->storage_total, nf->storage_free);
}

void luoyun_node_info_cleanup(NodeInfo * nf)
{
    if (nf == NULL)
        return;
    if (nf->cpu_model)
        free(nf->cpu_model);
    if (nf->host_name)
        free(nf->host_name);
    if (nf->host_ip)
        free(nf->host_ip);
    bzero(nf, sizeof(NodeInfo));
}

void luoyun_instance_info_print(InstanceInfo *ii)
{
    logsimple("Instance Info struct:\n"
              "ip = %s\n"
              "gport = %d\n"
              "status = %d\n",
              ii->ip, ii->gport, ii->status);
}

void luoyun_instance_info_cleanup(InstanceInfo *ii)
{
    if (ii == NULL)
        return;
    if (ii->ip)
        free(ii->ip);
    bzero(ii, sizeof(InstanceInfo));
}

void luoyun_osm_info_print(OSMInfo *oi)
{
    logsimple("Instance Info struct:\n"
              "ip = %s\n"
              "tag = %d\n"
              "status = %d\n",
              oi->ip, oi->tag, oi->status);
}

void luoyun_osm_info_cleanup(OSMInfo *oi)
{
    if (oi == NULL)
        return;
    if (oi->ip)
        free(oi->ip);
    bzero(oi, sizeof(OSMInfo));
    oi->tag = -1;
}

