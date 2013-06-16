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
#include <stddef.h>
#include <time.h>
#include <limits.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "../util/lyxml.h"
#include "../util/list.h"
#include "postgres.h"
#include "entity.h"
#include "node.h"
#include "lyclc.h"
#include "lyjob.h"

static LIST_HEAD(g_job_list);
static unsigned int g_job_count = 0;
static unsigned int g_job_ins_pending_nr = 0;

void job_print_queue()
{
    if (list_empty(&g_job_list)) {
        logdebug(_("job queue is empty\n"));
        return;
    }
    else
        logdebug(_("%d jobs are loaded from db\n"), g_job_count);;

    LYJobInfo *curr;
    list_for_each_entry(curr, &(g_job_list), j_list) {
        logsimple("job %d, target %d, target id %d\n",
                  curr->j_id, curr->j_target_type, curr->j_target_id);
    }
}

int job_exist(LYJobInfo * job)
{
    if (job == NULL)
        return 0;

    LYJobInfo *curr;
    list_for_each_entry(curr, &(g_job_list), j_list) {
        if (job->j_id == curr->j_id)
            return 1;
    }
    return 0;
}

int job_check(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    if (job->j_action == LY_A_NODE_QUERY_INSTANCE ||
        job->j_action == LY_A_NODE_QUERY ||
        job->j_action == LY_A_OSM_QUERY)
        return 0;

    LYJobInfo *curr;
    LYJobInfo *safe;
    /* if instance is being destroyed, don't do anything */
    list_for_each_entry_safe(curr, safe, &(g_job_list), j_list) {
    if (curr->j_target_type == job->j_target_type &&
        curr->j_target_id == job->j_target_id &&
        curr->j_action == LY_A_NODE_DESTROY_INSTANCE)
        return LY_S_CANCEL_TARGET_BUSY;
    }

    if (job->j_action == LY_A_CLC_ENABLE_NODE ||
        job->j_action == LY_A_CLC_DISABLE_NODE) {
        list_for_each_entry_safe(curr, safe, &(g_job_list), j_list) {
            if (curr->j_target_type == job->j_target_type &&
                curr->j_target_id == job->j_target_id &&
                (curr->j_action == LY_A_CLC_ENABLE_NODE ||
                 curr->j_action == LY_A_CLC_DISABLE_NODE)) {
                /* allow only one enable/disable job at a time */
                return LY_S_CANCEL_TARGET_BUSY;
            }
        }
    }
    else if (job->j_action == LY_A_NODE_RUN_INSTANCE) {
        list_for_each_entry_safe(curr, safe, &(g_job_list), j_list) {
            if (curr->j_target_type == job->j_target_type && 
                curr->j_target_id == job->j_target_id && 
                curr->j_action != LY_A_NODE_QUERY_INSTANCE)
                /* no any control action actvie before running instance */
                return LY_S_CANCEL_TARGET_BUSY;
        }
    }
    else if (job->j_action == LY_A_NODE_FULLREBOOT_INSTANCE) {
        list_for_each_entry_safe(curr, safe, &(g_job_list), j_list) {
            if (curr->j_target_type == job->j_target_type &&
                curr->j_target_id == job->j_target_id &&
                curr->j_action == job->j_action)
                /* no any control action actvie before running instance */
                return LY_S_CANCEL_TARGET_BUSY;
        }
    }
    else if (job->j_action == LY_A_NODE_DESTROY_INSTANCE) {
        list_for_each_entry_safe(curr, safe, &(g_job_list), j_list) {
            if (curr->j_target_type == job->j_target_type &&
                curr->j_target_id == job->j_target_id) {
                if (curr->j_action == job->j_action)
                    /* allow only one active destroy action at a time */
                    return LY_S_CANCEL_TARGET_BUSY;
                else if (curr->j_action != LY_A_NODE_STOP_INSTANCE)
                    /* any active action except stop should be cancelled */
                    job_update_status(curr, LY_S_CANCEL_ACTION_REPLACED);
            }
        }
    }
    else if (job->j_target_type == JOB_TARGET_INSTANCE) {
        /* for all other control action agaist instance */
        list_for_each_entry_safe(curr, safe, &(g_job_list), j_list) {
            if (curr->j_target_type == job->j_target_type &&
                curr->j_target_id == job->j_target_id) {
                if (curr->j_action == LY_A_NODE_QUERY_INSTANCE)
                    /* always allow query to go through */
                    continue;
                if (curr->j_action == job->j_action ||
                    JOB_IS_RUNNING(curr->j_status))
                    /* same action or other control action that's active */
                    return LY_S_CANCEL_TARGET_BUSY;
                else
                    /* inactive control action should be cancelled */
                    job_update_status(curr, LY_S_CANCEL_ACTION_REPLACED);
            }
        }
    }

    return 0;
}

LYJobInfo * job_find(int id)
{
    LYJobInfo *curr;
    list_for_each_entry(curr, &(g_job_list), j_list) {
        if (curr->j_id == id)
            return curr;
    }
    return NULL;
}

int job_insert(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    list_add_tail(&(job->j_list), &(g_job_list));
    g_job_count++;
    return 0;
}

int job_remove(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    list_del(&job->j_list);
    g_job_count--;
    free(job);
    return 0;
}

int job_busy_remove(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    if (job->j_pending_nr == 0) {
        job->j_pending_nr = -1; /* not busy */
        LYNodeData * nd = ly_entity_data(job->j_ent_id);
        if (nd != NULL && nd->ins_job_busy_nr > 0) {
            nd->ins_job_busy_nr--;
            logdebug(_("entity %d job busy nr %d\n"), job->j_ent_id, nd->ins_job_busy_nr);
        }
    }
    return 0;
}

int job_update_status(LYJobInfo * job, int status)
{
    if (JOB_IS_INITIATED(status))
        return 0;

    job->j_status = status;

    if (JOB_IS_STARTED(status))
        time(&job->j_started);

    if (JOB_IS_FINISHED(status) ||
        JOB_IS_TIMEOUT(status) ||
        JOB_IS_CANCELLED(status))
        time(&job->j_ended);

    if (db_job_update_status(job) < 0) {
        logerror(_("db error %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (status == LY_S_WAITING_STARTING_OSM) {
        InstanceInfo ii;
        bzero(&ii, sizeof(InstanceInfo));
        ii.ip = "0.0.0.0";
        ii.gport = 0;
        ii.status = DOMAIN_S_START;
        int node_id = ly_entity_db_id(job->j_ent_id);
        if (db_instance_update_status(job->j_target_id, &ii, node_id) < 0) {
            logerror(_("db error %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        job_busy_remove(job);
        return 0;
    }

    if (JOB_IS_FINISHED(status) ||
        JOB_IS_TIMEOUT(status) ||
        JOB_IS_CANCELLED(status)) {
        
        /* check whether any further action should be taken
        ** as a result of job status change
        */
        if (JOB_IS_CANCELLED(status) ||
            job->j_target_type != JOB_TARGET_INSTANCE) {
            job_remove(job);
            return 0;
        }

        /* update instance info */
        InstanceInfo ii;
        bzero(&ii, sizeof(InstanceInfo));
        int ret = 0;

        /* need to query status if timed out */
        if (JOB_IS_TIMEOUT(status)) {
            loginfo(_("job %d is timed out\n"), job->j_id);
            int ent_id = ly_entity_find_by_db(LY_ENTITY_OSM, job->j_target_id);
            if (ent_id > 0) {
                loginfo(_("release entity %d\n"), ent_id);
                ly_entity_release(ent_id);
            }
            ii.ip = NULL;
            ii.gport = 0;
            ii.status = DOMAIN_S_NEED_QUERY;
            ret = db_instance_update_status(job->j_target_id, &ii, -1);
            job_internal_query_instance(job->j_target_id);
            if (job->j_action == LY_A_NODE_RUN_INSTANCE)
                job_busy_remove(job);
        }
        else if ((job->j_action == LY_A_NODE_RUN_INSTANCE ||
                  job->j_action == LY_A_NODE_FULLREBOOT_INSTANCE) && 
                 status == LY_S_FINISHED_SUCCESS) {
            /* done while processing osm report
            int ent_id = ly_entity_find_by_db(LY_ENTITY_OSM, job->j_target_id);
            OSMInfo *oi = ly_entity_data(ent_id);
            ii.ip = oi->ip;
            ii.status = DOMAIN_S_SERVING;
            ii.gport = -1;
            int node_id = ly_entity_db_id(job->j_ent_id);
            ret = db_instance_update_status(job->j_target_id, &ii, node_id);
            */
            ret = 0;
            job_busy_remove(job);
        }
        else if (job->j_action == LY_A_NODE_STOP_INSTANCE &&
                 (status == LY_S_FINISHED_SUCCESS ||
                  status == LY_S_FINISHED_INSTANCE_NOT_RUNNING)) {
            logdebug(_("instance %d stopped\n"), job->j_target_id);
            int ent_id = ly_entity_find_by_db(LY_ENTITY_OSM, job->j_target_id);
            if (ent_id > 0) {
                loginfo(_("release entity %d\n"), ent_id);
                ly_entity_release(ent_id);
            }
            ii.ip = "0.0.0.0";
            ii.gport = 0;
            ii.status = DOMAIN_S_STOP;
            ret = db_instance_update_status(job->j_target_id, &ii, -1);
        }
        else if (job->j_action == LY_A_NODE_DESTROY_INSTANCE &&
                 status == LY_S_FINISHED_SUCCESS) {
            logdebug(_("delete instance %d\n"), job->j_target_id);
            ret = db_instance_delete(job->j_target_id);
        }

        job_remove(job);
        if (ret < 0)  {
            logerror(_("db error %s(%d)\n"), __func__, __LINE__);
            return ret;
        }
    }

    return 0;
}

static int __job_start_instance(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    logdebug(_("run job %d\n"), job->j_id);

    if (job->j_status == LY_S_WAITING_STARTING_OSM) {
        int ent_id = ly_entity_find_by_db(LY_ENTITY_OSM, job->j_target_id);
        if (ly_entity_is_online(ent_id)) {
            loginfo(_("instance %d is online\n"), job->j_target_id);
            job_update_status(job, LY_S_WAITING_SYCING_OSM);
        }
        return 0;
    }
    else if (job->j_status == LY_S_WAITING_SYCING_OSM) {
        int ent_id = ly_entity_find_by_db(LY_ENTITY_OSM, job->j_target_id);
        if (ly_entity_is_registered(ent_id)) {
            logdebug(_("instance %d started\n"), job->j_target_id);
            /* ly_entity_print_osm(); */
            job_update_status(job, LY_S_WAITING_STARTING_SERVICE);
        }
        else if (!ly_entity_is_online(ent_id)) {
             loginfo(_("instance %d is offline\n"), job->j_target_id);
             job_update_status(job, JOB_S_FAILED);
             return -1;
        }
        /* continue waiting */
        return 0;
    }
    else if (job->j_status == LY_S_WAITING_STARTING_SERVICE) {
        int ent_id = ly_entity_find_by_db(LY_ENTITY_OSM, job->j_target_id);
        if (ly_entity_is_running(ent_id)) {
            logdebug(_("instance %d started running\n"), job->j_target_id);
            job_update_status(job, JOB_S_FINISHED);
        }
        else if (!ly_entity_is_online(ent_id)) {
             loginfo(_("instance %d is offline\n"), job->j_target_id);
             job_update_status(job, JOB_S_FAILED);
             return -1;
        }
        /* continue waiting */
        return 0;
    }
 
    /* update job status to running */
    if (job_update_status(job, JOB_S_RUNNING) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    job->j_pending_nr = 0;

    int job_status = JOB_S_FAILED;
    int node_id = 0;
    NodeCtrlInstance ci;
    bzero(&ci, sizeof(NodeCtrlInstance));
    ci.req_id = job->j_id;
    ci.ins_id = job->j_target_id;
    if (db_node_instance_control_get(&ci, &node_id) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }
    /* ci.req_action = __job_get_target_action(job->j_action); */
    ci.req_action = job->j_action;
    ci.reply = LUOYUN_REQUEST_REPLY_RESULT | LUOYUN_REQUEST_REPLY_STATUS;

    int ent_id = node_schedule(node_id);
    if (ent_id == NODE_SCHEDULE_NODE_BUSY) {
        if (node_id)
            logwarn(_("failed to run instance %d. node %d busy!\n"), ci.ins_id, node_id);
        else
            logwarn(_("failed to run instance %d. node busy!\n"), ci.ins_id);
        job_status = LY_S_FINISHED_FAILURE_NODE_BUSY;
        goto failed;
    }
    else if (ent_id == NODE_SCHEDULE_NODE_STROKE) {
        g_job_ins_pending_nr++;
        if (node_id)
            loginfo(_("run instance %d pending(#%d). node %d stroke!\n"), ci.ins_id, g_job_ins_pending_nr, node_id);
        else
            loginfo(_("run instance %d pending(#%d). node stroke!\n"), ci.ins_id, g_job_ins_pending_nr);
        job_status = LY_S_PENDING_NODE_STROKE;
        job->j_pending_nr = g_job_ins_pending_nr;
        goto failed;
    }
    else if (ent_id < 0) {
        if (node_id) {
            ent_id = ly_entity_find_by_db(LY_ENTITY_NODE, node_id);
            if (!ly_entity_is_online(ent_id)) {
                logwarn(_("node %d is not online\n"), node_id);
                job_status = LY_S_FINISHED_FAILURE_NODE_NOT_ONLINE;
            }
            else if (!ly_entity_is_registered(ent_id)){
                logwarn(_("node %d is not regisered\n"), node_id);
                job_status = LY_S_FINISHED_FAILURE_NODE_NOT_REGISTERED;
            }
            else if (!ly_entity_is_enabled(ent_id)) {
                logwarn(_("node %d is not enabled\n"), node_id);
                job_status = LY_S_FINISHED_FAILURE_NODE_NOT_ENABLED;
            }
            else {
               logwarn(_("failed to run instance %d. no node!\n"), ci.ins_id);
               job_status = LY_S_FINISHED_FAILURE_NODE_NOT_AVAIL;
            }
        }
        else {
            logwarn(_("failed to run instance %d. no node!\n"), ci.ins_id);
            job_status = LY_S_FINISHED_FAILURE_NODE_NOT_AVAIL;
        }
        goto failed;
    }

    job->j_ent_id = ent_id;
    node_id = ly_entity_db_id(ent_id);
    loginfo(_("run instance %d on node %d entity %d\n"),
               ci.ins_id, node_id, ent_id);
    if (g_c->debug)
        luoyun_node_ctrl_instance_print(&ci);

    LYNodeData * nd = ly_entity_data(ent_id);
    if (nd == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }
    NodeInfo * nf = &nd->node;

    if (ci.ins_status == DOMAIN_S_NEW || ci.osm_secret == NULL) {
        if (ci.osm_secret)
            free(ci.osm_secret);
        ci.osm_secret = lyauth_secret();
        if (ci.osm_secret == NULL) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto failed;
        }
        if (db_instance_update_secret(ci.osm_tag, ci.osm_secret) < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto failed;
        }
    }

    if (db_instance_update_status(ci.ins_id, NULL, node_id) < 0) {
        logerror(_("db error %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    char *xml = lyxml_data_instance_run(&ci, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    logdebug(_("sending instance control request ...\n"));
    int len = strlen(xml);
    if (ly_packet_send(ly_entity_fd(ent_id),
                       PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST,
                       xml, len) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        free(xml);
        goto failed;
    }

    /* update the number of instance start jobs */
    nd->ins_job_busy_nr++;
 
    /* temprarily hold the resource, recovered automatically in case of failure */
    nf->cpu_commit += ci.ins_vcpu;
    nf->mem_commit += ci.ins_mem;

    free(xml);
    luoyun_node_ctrl_instance_cleanup(&ci);

    return 0;

failed:
    luoyun_node_ctrl_instance_cleanup(&ci);
    if (job_update_status(job, job_status) < 0)
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
    return -1;
}

static int __job_control_instance_simple(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    logdebug(_("run job %d\n"), job->j_id);

    if (job_update_status(job, JOB_S_RUNNING) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int node_id = 0;
    NodeCtrlInstance ci;
    bzero(&ci, sizeof(NodeCtrlInstance));
    ci.req_id = job->j_id;
    ci.ins_id = job->j_target_id;
    if (db_node_instance_control_get(&ci, &node_id) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }
    /* ci.req_action = __job_get_target_action(job->j_action); */
    ci.req_action = job->j_action;
    ci.reply = LUOYUN_REQUEST_REPLY_RESULT;
    if (g_c->debug)
        luoyun_node_ctrl_instance_print(&ci);

    if (node_id <= 0) {
        logwarn(_("no node found for job %d\n"), job->j_id);
        luoyun_node_ctrl_instance_cleanup(&ci);
        if (job->j_action == LY_A_NODE_QUERY_INSTANCE) {
            InstanceInfo ii;
            bzero(&ii, sizeof(InstanceInfo));
            ii.ip = "0.0.0.0";
            ii.gport = 0;
            ii.status = DOMAIN_S_NOT_EXIST;
            db_instance_update_status(job->j_target_id, &ii, node_id);
        }
        job_update_status(job, JOB_S_FINISHED);
        return 0;
    }
    logdebug(_("send job to node %d\n"), node_id);

    int ent_id = ly_entity_find_by_db(LY_ENTITY_NODE, node_id);
    logdebug(_("run on entity %d\n"), ent_id);
    if (ly_entity_is_online(ent_id) == 0) {
        logerror(_("try to control instance(%d), "
                   "but the node(%d) is not online.\n"),
                   ci.ins_id, node_id);
        goto failed;
    }
    if (ly_entity_is_registered(ent_id) == 0) {
        logerror(_("try to control instance(%d), "
                   "but the node(%d) is not registered\n"),
                   ci.ins_id, node_id);
        goto failed;
    }
    job->j_ent_id = ent_id;

    char *xml = lyxml_data_instance_other(&ci, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }
    logdebug(_("sending instance control request ...\n"));
    int len = strlen(xml);
    if (ly_packet_send(ly_entity_fd(ent_id),
                       PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST,
                       xml, len) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        free(xml);
        goto failed;
    }
    free(xml);

    luoyun_node_ctrl_instance_cleanup(&ci);
    return 0;

failed:
    luoyun_node_ctrl_instance_cleanup(&ci);
    job_update_status(job, JOB_S_FAILED);
    return -1;
}

static int __job_query_node(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    logdebug(_("run job %d\n"), job->j_id);

    if (job_update_status(job, JOB_S_RUNNING) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int node_id = job->j_target_id;
    int ent_id = ly_entity_find_by_db(LY_ENTITY_NODE, node_id);
    logdebug(_("run on entity %d\n"), ent_id);
    if (ly_entity_is_online(ent_id) == 0) {
        loginfo(_("query node %d: node is not online.\n"), node_id);
        job_update_status(job, JOB_S_FINISHED);
        return 0;
    }
    if (ly_entity_is_registered(ent_id) == 0) {
        loginfo(_("query node %d: node is not registered\n"), node_id);
        job_update_status(job, JOB_S_FINISHED);
        return 0;
    }
    job->j_ent_id = ent_id;

    char *xml = lyxml_data_node_info(job->j_id, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto failed;
    }

    logdebug(_("sending node query request ...\n"));
    int len = strlen(xml);
    if (ly_packet_send(ly_entity_fd(ent_id),
                       PKT_TYPE_CLC_NODE_CONTROL_REQUEST,
                       xml, len) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        free(xml);
        goto failed;
    }

    free(xml);
    return 0;

failed:
    job_update_status(job, JOB_S_FAILED);
    return -1;
}

/* enable a new node */
int __job_node_enable(LYJobInfo * job)
{
    int ent_id= ly_entity_find_by_db(LY_ENTITY_NODE, job->j_target_id);
    logdebug(_("enable node %d on entity %d\n"), job->j_target_id, ent_id);

    /* node has to be online to enable */
    if (!ly_entity_is_online(ent_id)) {
        ly_mcast_send_join();
        job_update_status(job, JOB_S_FAILED);
        return 0;
    }

    /* node status also got reset */
    if (db_node_enable(job->j_target_id, 1) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        job_update_status(job, JOB_S_FAILED);
        return -1;
    }

    int fd = ly_entity_fd(ent_id);
    if (ly_packet_send(fd, PKT_TYPE_JOIN_REQUEST, "join", 4) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        job_update_status(job, JOB_S_FAILED);
        return -1;
    }
    job_update_status(job, JOB_S_FINISHED);
    return 0;
}

/* disable a node */
int __job_node_disable(LYJobInfo * job)
{
    logdebug(_("disable node %d\n"), job->j_target_id);

    /* node status also got reset */
    if (db_node_enable(job->j_target_id, 0) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        job_update_status(job, JOB_S_FAILED);
        return -1;
    }

    int ent_id= ly_entity_find_by_db(LY_ENTITY_NODE, job->j_target_id);
    if (ly_entity_is_online(ent_id)) {
        logdebug(_("node %d is online. disable it\n"), job->j_target_id);
        ly_entity_enable(ent_id, -1, 0);
    }
    else {
        logdebug(_("node %d is not online\n"), job->j_target_id);
    }

    job_update_status(job, JOB_S_FINISHED);
    return 0;
}

/* node config */
int __job_node_config(LYJobInfo * job)
{
    int ent_id= ly_entity_find_by_db(LY_ENTITY_NODE, job->j_target_id);
    logdebug(_("config node %d on entity %d\n"), job->j_target_id, ent_id);

    /* node has to be online first */
    if (!ly_entity_is_online(ent_id))
        goto done;

    LYNodeData * nd = ly_entity_data(ent_id);
    if (nd == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto fail;
    }
    NodeInfo * nf = &nd->node;

    DBNodeRegInfo db_nf;
    bzero(&db_nf, sizeof(DBNodeRegInfo));
    int db_id = ly_entity_db_id(ent_id);

    if (db_node_find(DB_NODE_FIND_BY_ID, &db_id, &db_nf) == 1) {
        nf->cpu_vlimit = db_nf.cpu_vlimit;
        nf->mem_vlimit = db_nf.mem_vlimit;
        loginfo(_("node config: %d %d\n"), nf->cpu_vlimit, nf->mem_vlimit);
        goto done;
    }
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto fail;
   }

done:
    job_update_status(job, JOB_S_FINISHED);
    return 0;
fail:
    job_update_status(job, JOB_S_FAILED);
    return -1;
}


/* query osm */
static int __job_query_osm(LYJobInfo * job)
{
    if (job == NULL)
        return -1;

    logdebug(_("run job %d\n"), job->j_id);

    if (job_update_status(job, JOB_S_RUNNING) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int ins_id = job->j_target_id;
    int ent_id = ly_entity_find_by_db(LY_ENTITY_OSM, ins_id);
    logdebug(_("run on entity %d\n"), ent_id);
    if (ly_entity_is_online(ent_id) == 0) {
        loginfo(_("query instance %d: instance is not online\n"), ins_id);
        job_update_status(job, JOB_S_FINISHED);
        return 0;
    }
    if (ly_entity_is_registered(ent_id) == 0) {
        loginfo(_("query instance %d: instance is not registered\n"), ins_id);
        job_update_status(job, JOB_S_FINISHED);
        return 0;
    }
    job->j_ent_id = ent_id;

    int fd = ly_entity_fd(ent_id);
    if (ly_packet_send(fd, PKT_TYPE_CLC_OSM_QUERY_REQUEST,
                       &job->j_id, sizeof(job->j_id)) < 0) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        job_update_status(job, JOB_S_FAILED);
        return -1;
    }

    return 0;
}

static int __job_run(LYJobInfo * job)
{
    switch (job->j_action) {

    case LY_A_CLC_ENABLE_NODE:
        logdebug(_("run job, node enable.\n"));
        __job_node_enable(job);
        break;

    case LY_A_CLC_DISABLE_NODE:
        logdebug(_("run job, node disable.\n"));
        __job_node_disable(job);
        break;

    case LY_A_CLC_CONFIG_NODE:
        logdebug(_("run job, node config.\n"));
        __job_node_config(job);
        break;

    case LY_A_NODE_RUN_INSTANCE:
        logdebug(_("run job, instance start.\n"));
        __job_start_instance(job);
        break;

    case LY_A_NODE_FULLREBOOT_INSTANCE:
        logdebug(_("run job, instance reboot.\n"));
        __job_start_instance(job);
        break;

    case LY_A_NODE_STOP_INSTANCE:
    case LY_A_NODE_SUSPEND_INSTANCE:
    case LY_A_NODE_ACPIREBOOT_INSTANCE:
    case LY_A_NODE_DESTROY_INSTANCE:
    case LY_A_NODE_QUERY_INSTANCE:
        logdebug(_("run job, instance %s.\n"),
                   job->j_action == LY_A_NODE_QUERY_INSTANCE? "query" :
                   job->j_action == LY_A_NODE_STOP_INSTANCE? "stop" :
                   job->j_action == LY_A_NODE_DESTROY_INSTANCE? "destroy" :
                   job->j_action == LY_A_NODE_ACPIREBOOT_INSTANCE? "acpi-reboot" :
                   job->j_action == LY_A_NODE_SUSPEND_INSTANCE? "suspend" :
                   "unknown");
        __job_control_instance_simple(job);
        break;

    case LY_A_NODE_QUERY:
        __job_query_node(job);
        break;

    case LY_A_NODE_SAVE_INSTANCE:
        logerror(_("run job, not implemented.\n"));
        break;

    case LY_A_OSM_QUERY:
        __job_query_osm(job);
        break;

    default:
        logerror(_("run job, unknown job(%d %d %d).\n"), job->j_id, job->j_status, job->j_action);
        job_update_status(job, JOB_S_FAILED);
        return -1;
    }

    return 0;
}

int job_dispatch(void)
{
    int timeout;
    time_t now;
    now = time(&now);
    g_job_ins_pending_nr = 0;

    LYJobInfo *job;
    LYJobInfo *safe;
    list_for_each_entry_safe(job, safe, &(g_job_list), j_list) {
        if (JOB_IS_INITIATED(job->j_status)) {
            time(&job->j_last_run);
            __job_run(job);
        }
        else if (JOB_IS_RUNNING(job->j_status) ||
                 JOB_IS_WAITING(job->j_status) ||
                 JOB_IS_PENDING(job->j_status)) {
            if (job->j_target_type == JOB_TARGET_INSTANCE)
                timeout = g_c->job_timeout_instance;
            else if (job->j_target_type == JOB_TARGET_NODE)
                timeout = g_c->job_timeout_node;
            else
                timeout = g_c->job_timeout_other;
            if (JOB_IS_PENDING(job->j_status)) {
                if ((now - job->j_last_run) > (CLC_JOB_DISPATCH_INTERVAL)<<1) {
                    /* interval of checking pending jobs needs further research */
                    time(&job->j_last_run);
                    __job_run(job);
                }
            }
            else if ((now - job->j_started) > timeout) {
                logwarn(_("job %d timed out\n"), job->j_id);
                job_update_status(job, JOB_S_TIMEOUT);
            }
            else if (JOB_IS_WAITING(job->j_status))
                __job_run(job);
        }
        else {
            logerror(_("in %s, job %d in unexpected status(%d)\n"),
                        __func__, job->j_id, job->j_status);
            /* user intervention is required */
            job_update_status(job, JOB_S_UNKNOWN);
        }
    }
    return 0;
}

int job_init(void)
{
    INIT_LIST_HEAD(&g_job_list);

    int ret = db_job_get_all();
    if (ret < 0) {
        job_cleanup();
        return -1;
    }

    g_job_count = (unsigned int) ret;

    /* init instance status in db */
    db_instance_init_status();
    db_node_init_status();

    return 0;
}

void job_cleanup(void)
{
    LYJobInfo *job;
    LYJobInfo *tmp;
    list_for_each_entry_safe(job, tmp, &(g_job_list), j_list) {
        logdebug(_("deleting job %d\n"), job->j_id);
        list_del(&(job->j_list));
        free(job);
    }
    return;
}
