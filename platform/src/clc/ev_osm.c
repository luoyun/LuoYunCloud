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
#include <limits.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "../util/lyutil.h"
#include "../util/misc.h"
#include "entity.h"
#include "lyjob.h"
#include "postgres.h"
#include "lyclc.h"

/* process osm query */
int eh_process_osm_query(char *buf)
{
    logdebug(_("%s called\n"), __func__);
    logdebug(_("response for osm query request, <%s>\n"), buf);

    int job_id, osm_tag, osm_status;
    char ip[MAX_IP_LEN];
    if (sscanf(buf, "%d %d %d %s", &job_id, &osm_tag, &osm_status, ip) != 4) {
        logerror(_("osm query returns unexpected data\n"));
        return 1;
    }

    LYJobInfo * job = job_find(job_id);
    if (job == NULL) {
        logwarn(_("job(%d) not found in %s\n"), job_id, __func__);
        return 0;
    }

    loginfo(_("osm(tag:%d ip:%s) status %d\n"), osm_tag, ip, osm_status);

    if (job_update_status(job, LY_S_FINISHED_SUCCESS)) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return 0;
}

/* process osm report */
int eh_process_osm_report(char * buf, int size, int ent_id)
{
    logdebug(_("%s called\n"), __func__);

    if (size != sizeof(int32_t)) {
        logerror(_("unexpected osm report data size\n"));
        return -1;
    }

    int status = *(int32_t *)buf;
    logdebug(_("osm report: <%d>\n"), status);
    if (status == LY_S_APP_RUNNING) {
        loginfo(_("osm report: %d, %s\n"), status, "application running");
        if (!ly_entity_is_serving(ent_id)) {
            int db_id = ly_entity_db_id(ent_id);
            InstanceInfo ii;
            ii.status = DOMAIN_S_SERVING;
            ii.ip = NULL;
            if (db_instance_update_status(db_id, &ii, -1) < 0) {
                logerror(_("error in %s(%d)\n"), __func__, __LINE__);
                return -1;
            }

            ly_entity_update(ent_id, -1, LY_ENTITY_FLAG_STATUS_SERVING);
            loginfo(_("instance (tag:%d) is servicing\n"), db_id);
        }
    }
    else if (status == LY_S_APP_UNKNOWN) {
        loginfo(_("osm report: %d, %s\n"), status, "application no status");
        if (!ly_entity_is_running(ent_id) || ly_entity_is_serving(ent_id)) {
            int db_id = ly_entity_db_id(ent_id);
            InstanceInfo ii;
            ii.status = DOMAIN_S_RUNNING;
            ii.ip = NULL;
            if (db_instance_update_status(db_id, &ii, -1) < 0) {
                logerror(_("error in %s(%d)\n"), __func__, __LINE__);
                return -1;
            }

            ly_entity_update(ent_id, -1, LY_ENTITY_FLAG_STATUS_RUNNING);
            loginfo(_("instance (tag:%d) is running\n"), db_id);
        }
    }
    else {
        loginfo(_("osm report: %d, %s\n"), status, "application state unknown");
        if (ly_entity_is_serving(ent_id)) {
            int db_id = ly_entity_db_id(ent_id);
            InstanceInfo ii;
            ii.status = DOMAIN_S_RUNNING;
            ii.ip = NULL;
            if (db_instance_update_status(db_id, &ii, -1) < 0) {
                logerror(_("error in %s(%d)\n"), __func__, __LINE__);
                return -1;
            }

            ly_entity_update(ent_id, -1, LY_ENTITY_FLAG_STATUS_REGISTERED);
            loginfo(_("instance (tag:%d) is running without web serving\n"), db_id);
        }
    }
    return 0;
}

/* process register request from instance */
int eh_process_osm_register(char * buf, int size, int ent_id)
{
    logdebug(_("%s called\n"), __func__);
    logdebug(_("osm register request, <%s>\n"), buf);

    if (ly_entity_is_registered(ent_id)) {
        logwarn(_("received osm register request again, ignored\n"));
        return -1;
    }

    OSMInfo * oi = ly_entity_data(ent_id);
    if (oi == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    char ip[MAX_IP_LEN];
    if (sscanf(buf, "%d %d %s", &oi->tag, &oi->status, ip) != 3) {
        logerror(_("osm register with unexpected data\n"));
        return 1;
    }
    oi->ip = strdup(ip);

    int result = LY_S_REGISTERING_DONE_SUCCESS;
    if (ly_entity_is_authenticated(ent_id) == 0) {
        logwarn(_("OSM(%d %d %s) not authenticated\n"),
                  oi->tag, oi->status, ip);
        result = LY_S_REGISTERING_DONE_FAIL;
    }
    else if (oi->status != OSM_STATUS_UNREGISTERED) {
        logwarn(_("OSM(%d %d %s) register with unexpected status\n"),
                  oi->tag, oi->status, ip);
        result = LY_S_REGISTERING_DONE_FAIL;
    }

    int fd = ly_entity_fd(ent_id);
    if (ly_packet_send(fd, PKT_TYPE_OSM_REGISTER_REPLY,
                       &result, sizeof(result)) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (result != LY_S_REGISTERING_DONE_SUCCESS)
        return 0;

    InstanceInfo ii;
    ii.status = DOMAIN_S_RUNNING;
    ii.ip = ip;
    if (db_instance_update_status(oi->tag, &ii, -1) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    ly_entity_update(ent_id, oi->tag, LY_ENTITY_FLAG_STATUS_REGISTERED);
    loginfo(_("instance (tag:%d, ip:%s) registered successfully\n"),
              oi->tag, ip);

#if 0
    /* prepare storage for the instance */
    int ins_id = oi->tag;
    char cmd[PATH_MAX];
    snprintf(cmd, PATH_MAX, "exportfs -o rw,no_root_squash %s:/%s/%d",
                    ip, g_c->clc_data_dir, ins_id);
         
    if (system_call(cmd))
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
#endif    
    return 0;
}

/* process raw auth request from osmanager */
int eh_process_osm_auth(int is_reply, void * data, int ent_id)
{
    logdebug(_("%s called\n"), __func__);

    int ret;
    AuthInfo * ai = data;
    AuthConfig * ac = ly_entity_auth(ent_id);

    if (is_reply) {
        loginfo(_("auth reply from instance %d(tag)\n"), ai->tag);
        ret = lyauth_verify(ac, ai->data, LUOYUN_AUTH_DATA_LEN);
        if (ret < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        if (ret) {
            loginfo(_("node %d(tag) is authenticated\n"), ai->tag);
            if (!ly_entity_is_authenticated(ent_id))
                ly_entity_update(ent_id, -1, LY_ENTITY_FLAG_STATUS_AUTHENTICATED);
        }
        else {
            logwarn(_("chanllenge verification for node %d(tag) failed.\n"),
                      ai->tag);
            return 1;
        }
        return 0;
    }

    loginfo(_("auth request from instance %d(tag)\n"), ai->tag);

    OSMInfo * oi = ly_entity_data(ent_id);
    if (oi == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* get secret */
    if (ac->secret == NULL) {
        logdebug(_("retrieve auth key for instance %d(tag)\n"), ai->tag);
        ret = db_instance_find_secret(ai->tag, &ac->secret);
        if (ret < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        else if (ret == 0) {
            logerror(_("instance(tag: %d) not in db\n"), ai->tag);
            return -1;
        }
        oi->tag = ai->tag;
    }

    /* resolve challenge */
    logdebug(_("answer auth request\n"));
    ret = lyauth_answer(ac, ai->data, LUOYUN_AUTH_DATA_LEN);
    if (ret < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* send answer back */
    int fd = ly_entity_fd(ent_id);
    if (ly_packet_send(fd, PKT_TYPE_OSM_AUTH_REPLY,
                       ai, sizeof(AuthInfo)) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* request challenging */
    logdebug(_("clc prepare auth request\n"));
    if (lyauth_prepare(ac) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    logdebug(_("clc prepare auth packet\n"));
    bzero(ai->data, LUOYUN_AUTH_DATA_LEN);
    strncpy((char *)ai->data, ac->challenge, LUOYUN_AUTH_DATA_LEN);
    logdebug(_("clc sends out auth request\n"));
    if (ly_packet_send(fd, PKT_TYPE_OSM_AUTH_REQUEST,
                       ai, sizeof(AuthInfo)) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    loginfo(_("instance %d(tag) is online\n"), oi->tag);
    ly_entity_update(ent_id, oi->tag, LY_ENTITY_FLAG_STATUS_ONLINE);

    return 0;
}

