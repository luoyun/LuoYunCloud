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
#include <pthread.h>
#include <libpq-fe.h>

#include "../util/logging.h"
#include "../luoyun/luoyun.h"
#include "lyclc.h"
#include "lyjob.h"
#include "postgres.h"

PGconn * _db_conn = NULL;
pthread_mutex_t _db_lock;

static PGresult * __db_select(char *sql)
{
    PGresult *res;

    pthread_mutex_lock(&_db_lock);
    res = PQexec(_db_conn, sql);
    pthread_mutex_unlock(&_db_lock);

    if (PQresultStatus(res) != PGRES_TUPLES_OK) {
        logerror(_("db exec failed: %s\n"), PQerrorMessage(_db_conn));
        PQclear(res);
        return NULL;
    }

    return res;
}

static int __db_exec(char *sql)
{
    PGresult *res;

    pthread_mutex_lock(&_db_lock);
    res = PQexec(_db_conn, sql);
    pthread_mutex_unlock(&_db_lock);

    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        logerror(_("db exec failed: %s\n"), PQerrorMessage(_db_conn));
        PQclear(res);
        return -1;
    }

    PQclear(res);
    return 0;
}

/* return db id if exists */
int db_node_exist(int type, void * data)
{
    if (data == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);        
        return -1;
    }

    int ret;
    char sql[LINE_MAX];
    if (type == DB_NODE_FIND_BY_IP)
        ret = snprintf(sql, LINE_MAX,
                       "SELECT id from node where ip = '%s';", (char *)data);
    else if (type == DB_NODE_FIND_BY_ID)
        ret = snprintf(sql, LINE_MAX,
                       "SELECT id from node where id = %d;", *(int *)data);
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);        
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;

    ret = PQntuples(res);
    if (ret > 1) {
        logerror(_("DB have multi node with same tag\n"));
        ret = -1;
    }
    else if (ret == 1) {
        ret = atoi(PQgetvalue(res, 0, 0));
        if (ret <= 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            ret = -1;
        }
    }

    PQclear(res);
    return ret;
}

/* return db id if exists */
int db_node_find_secret(int type, void * data, char ** secret)
{
    if (data == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int ret;
    char sql[LINE_MAX];
    if (type == DB_NODE_FIND_BY_IP)
        ret = snprintf(sql, LINE_MAX,
                       "SELECT id, key from node where ip = '%s';",
                       (char *)data);
    else if (type == DB_NODE_FIND_BY_ID)
        ret = snprintf(sql, LINE_MAX,
                       "SELECT id, key from node where id = %d;",
                       *(int *)data);
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;

    ret = PQntuples(res);
    if (ret > 1) {
        logerror(_("DB have multi node with same tag\n"));
        ret = -1;
    }
    else if (ret == 1) {
        ret = atoi(PQgetvalue(res, 0, 0));
        if (ret <= 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            ret = -1;
        }
        char * s = PQgetvalue(res, 0, 1);
        if (s && strlen(s))
            *secret = strdup(s);
    }

    PQclear(res);
    return ret;
}

/* return the number of entries found */
int db_node_find(int type, void * data, DBNodeRegInfo * db_nf)
{
    if (data == NULL || db_nf == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);        
        return -1;
    }

    int ret;
    char sql[LINE_MAX];
    if (type == DB_NODE_FIND_BY_IP)
        ret = snprintf(sql, LINE_MAX,
                       "SELECT id, status, ip, key, vcpus, vmemory, isenable from node "
                       "where ip = '%s' order by key DESC;", (char *)data);
    else if (type == DB_NODE_FIND_BY_ID)
        ret = snprintf(sql, LINE_MAX,
                       "SELECT id, status, ip, key, vcpus, vmemory, isenable from node "
                       "where id = %d order by key DESC;", *(int *)data);
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);        
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;

    ret = PQntuples(res);
    if (ret >= 1) {
        db_nf->id = atoi(PQgetvalue(res, 0, 0));
        db_nf->status = atoi(PQgetvalue(res, 0, 1));
        char * s = PQgetvalue(res, 0, 2);
        if (s && strlen(s))
            db_nf->ip = strdup(s);
        s = PQgetvalue(res, 0, 3);
        if (s && strlen(s))
            db_nf->secret = strdup(s);
        db_nf->cpu_vlimit = atoi(PQgetvalue(res, 0, 4));
        db_nf->mem_vlimit = atoi(PQgetvalue(res, 0, 5));
        s = PQgetvalue(res, 0, 6);
        db_nf->enabled = s[0] == 't' ? 1 : 0;
    }
    if (ret > 1) {
        char * s = PQgetvalue(res, 1, 3);
        if (s && strlen(s))
            ret = 1;
        /* do not allow more than 1 entry with same ip and NULL key */
    }
    if (ret > 1)
        logerror(_("DB have multi node with same tag\n"));

    PQclear(res);
    return ret;
}

int db_node_reginfo_free(DBNodeRegInfo * nf)
{
    if (nf == NULL)
        return -1;
    if (nf->ip)
        free(nf->ip);
    if (nf->secret)
        free(nf->secret);
    return 0;
}

int db_node_update_secret(int type, void * data, char * secret)
{
    if (data == NULL || secret == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int ret;
    char sql[LINE_MAX];
    if (type == DB_NODE_FIND_BY_ID)
        ret = snprintf(sql, LINE_MAX,
                       "UPDATE node SET key = '%s', " 
                       "updated = 'now' WHERE id= %d;",
                       secret, *(int *)data);
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return __db_exec(sql);
}

int db_node_update(int type, void * data, NodeInfo * nf) 
{
    if (data == NULL || nf == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int ret;
    char sql[LINE_MAX];
    if (type == DB_NODE_FIND_BY_IP)
        ret = snprintf(sql, LINE_MAX,
                       "UPDATE node SET memory = %d, "
                       "hostname = '%s', arch = %d, cpus = %d, "
                       "cpu_model = '%s', cpu_mhz = %d, status = %d, "
                       "updated = 'now' WHERE ip = '%s';",
                       nf->mem_max,
                       nf->host_name, nf->cpu_arch, nf->cpu_max,
                       nf->cpu_model, nf->cpu_mhz, nf->status,
                       nf->host_ip);
    else if (type == DB_NODE_FIND_BY_ID)
        ret = snprintf(sql, LINE_MAX,
                       "UPDATE node SET memory = %d, "
                       "hostname = '%s', arch = %d, cpus = %d, "
                       "cpu_model = '%s', cpu_mhz = %d, status = %d, "
                       "ip = '%s', updated = 'now' WHERE id = %d;",
                       nf->mem_max,
                       nf->host_name, nf->cpu_arch, nf->cpu_max,
                       nf->cpu_model, nf->cpu_mhz, nf->status,
                       nf->host_ip, *(int *)data);
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return __db_exec(sql);
}

int db_node_enable(int id, int enable)
{
    char sql[LINE_MAX];
    int ret = snprintf(sql, LINE_MAX,
                       "UPDATE node SET isenable = '%s', "
                       "updated = 'now' WHERE id= %d;",
                       enable ? "True" : "False", id);

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return __db_exec(sql);
}

/* upon successful completion, id of new entry is returned */
int db_node_insert(NodeInfo * nf)
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX,
                 "INSERT INTO node (id, hostname, ip, arch, memory, "
                 "status, cpus, cpu_model, "
                 "vcpus, vmemory, "
                 "cpu_mhz, created, updated) "
                 "VALUES (nextval('node_id_seq'), '%s', '%s', %d, %d, "
                 "%d, %d, '%s', "
                 "%d, %d, "
                 "%d, 'now', 'now');",
                 nf->host_name, nf->host_ip, nf->cpu_arch, nf->mem_max,
                 nf->status, nf->cpu_max, nf->cpu_model,
                 nf->cpu_vlimit, nf->mem_vlimit,
                 nf->cpu_mhz) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);        
        return -1;
    }
    if (__db_exec(sql) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (snprintf(sql, LINE_MAX,
                 "SELECT id from node where ip = '%s' order by id DESC; ",
                 nf->host_ip) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;
    int ret = atoi(PQgetvalue(res, 0, 0));
    PQclear(res);
    return ret;
}

int db_node_update_status(int type, void * data, int status)
{
    if (data == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    int ret;
    char sql[LINE_MAX];
    if (type == DB_NODE_FIND_BY_ID)
        ret = snprintf(sql, LINE_MAX,
                       "UPDATE node SET status = %d, "
                       "updated = 'now' WHERE id= %d;",
                       status, *(int *)data);
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    return __db_exec(sql);
}

int db_job_get(LYJobInfo * job)
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX,
                 "SELECT status, "
                 "extract(epoch FROM created), "
                 "extract(epoch FROM started), "
                 "extract(epoch FROM ended), "
                 "target_type, target_id, action "
                 "from job where id = %d;",
                 job->j_id) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;

    int ret = PQntuples(res);
    if (ret == 1) {
        job->j_status = atoi(PQgetvalue(res, 0, 0));
        job->j_created = atol(PQgetvalue(res, 0, 1));
        job->j_started = atol(PQgetvalue(res, 0, 2));
        job->j_ended = atol(PQgetvalue(res, 0, 3));
        job->j_target_type = atoi(PQgetvalue(res, 0, 4));
        job->j_target_id = atoi(PQgetvalue(res, 0, 5));
        job->j_action = atoi(PQgetvalue(res, 0, 6));
        logdebug(_("new job from db %d %d %d\n"), job->j_id, job->j_status, job->j_action);
        ret = 0;
    }
    else if (ret > 1) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        ret = -1;
    }
    else {
        logerror(_("no record for job %d in db\n"), job->j_id);
        ret = -1;
    }

    PQclear(res);
    return ret;
}

int db_job_get_all(void)
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX,
                 "SELECT id, status, "
                 "extract(epoch FROM created), "
                 "extract(epoch FROM started), "
                 "target_type, target_id, action "
                 "from job "
                 "where status >= %d and status < %d;",
                 LY_S_PENDING, LY_S_PENDING_LAST_STATUS) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;

    int ret = PQntuples(res);
    int r;
    for (r = 0; r < ret; r++) {
        LYJobInfo * job = malloc(sizeof(LYJobInfo));
        if (job == NULL)
            return -1;
        bzero(job, sizeof(LYJobInfo));
        job->j_id = atoi(PQgetvalue(res, r, 0));
        job->j_status = atoi(PQgetvalue(res, r, 1));
        job->j_created = atol(PQgetvalue(res, r, 2));
        job->j_started = atol(PQgetvalue(res, r, 3));
        job->j_target_type = atoi(PQgetvalue(res, r, 4));
        job->j_target_id = atoi(PQgetvalue(res, r, 5));
        job->j_action = atoi(PQgetvalue(res, r, 6));
        job_insert(job);
    }

    PQclear(res);
    return ret;
}

int db_job_update_status(LYJobInfo * job)
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX,
                 "UPDATE job SET status = %d, "
                 "started = %ld::abstime::timestamp, "
                 "ended = %ld::abstime::timestamp "
                 "WHERE status != %d and id = %d;",
                  job->j_status, (long)job->j_started, (long)job->j_ended,
                  job->j_status, job->j_id) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    return __db_exec(sql);

}

int db_instance_find_secret(int id, char ** secret)
{
    *secret = NULL;

    char sql[LINE_MAX];
    int ret = snprintf(sql, LINE_MAX,
                       "SELECT key from instance where id = %d;",
                       id);

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;

    ret = PQntuples(res);
    if (ret > 1) {
        logerror(_("DB have multi instance with same id %d\n"), id);
        ret = -1;
    }
    else if (ret == 1) {
        char * s = PQgetvalue(res, 0, 0);
        if (s && strlen(s)) {
            char * str = strdup(s);
            char * str1 = index(str, ':');
            if (str1)
                *str1 = '\0';
            *secret = strdup(str);
            free(str);
        }
    }

    PQclear(res);
    return ret;
}

int db_instance_update_secret(int id, char * secret)
{
    if (secret == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    char sql[LINE_MAX];
    int ret = snprintf(sql, LINE_MAX,
                       "SELECT key from instance where id = %d;",
                       id);

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;

    char * str = NULL, * saveptr1 = NULL;
    ret = PQntuples(res);
    if (ret > 1) {
        logerror(_("DB have multi instance with same id %d\n"), id);
        ret = -1;
        goto done;
    }
    else if (ret == 1) {
        char * s = PQgetvalue(res, 0, 0);
        if (s && strlen(s)) {
            str = strdup(s);
            saveptr1 = index(str, ':');
            if (saveptr1) {
                *saveptr1 = '\0';
                saveptr1++;
            }
            if (strcmp(str, secret) == 0) {
                ret = 0;
                goto done;
            }
        }
    }
    if (saveptr1)
        ret = snprintf(sql, LINE_MAX,
                       "UPDATE instance SET key = '%s:%s', "
                       "updated = 'now' WHERE id= %d;",
                       secret, saveptr1, id);
    else
        ret = snprintf(sql, LINE_MAX,
                       "UPDATE instance SET key = '%s', "
                       "updated = 'now' WHERE id= %d;",
                       secret, id);
    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        ret = -1;
        goto done;
    }

    ret = __db_exec(sql);
done:
    PQclear(res);
    if (str)
        free(str);
    return ret;
}

int db_instance_update_status(int instance_id, InstanceInfo * ii, int node_id)
{
    char sql[LINE_MAX];
    int ret = snprintf(sql, LINE_MAX,
                       "SELECT key, ip, node_id, status from instance where id = %d;",
                       instance_id);

    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    char s_key[128], s_ip[100], s_status[20], s_node_id[20];
    s_key[0] = '\0';
    s_ip[0] = '\0';
    s_node_id[0] = '\0';
    s_status[0] = '\0';
    ret = PQntuples(res);
    if (ret > 1) {
        logerror(_("DB have multi instance(%d) with same tag\n"), instance_id);
        PQclear(res);
        return -1;
    }
    else if (ret == 1) {
        if (ii) {
            char * s = PQgetvalue(res, 0, 0);
            char * str = NULL, *savestr = NULL, * ptr[6];
            int i;
            if (s && strlen(s)) {
                str = strdup(s);
                savestr = str;
            }
            for (i=0; i<6; i++) { 
                ptr[i] = NULL;
                if (str && strlen(str)) {
                    ptr[i] = str;
                    str = index(str, ':');
                    if (str) {
                        *str = '\0';
                        str++;
                    }
                }
            }
            int gport = 0;
            unsigned long pre1 = 0, pre2 = 0;
            unsigned long sum1 = 0, sum2 = 0;
            if (ptr[1])
                gport = atoi(ptr[1]);
            if (ptr[2])
                sum1 = atol(ptr[2]);
            if (ptr[3])
                pre1 = atol(ptr[3]);
            if (ptr[4])
                sum2 = atol(ptr[4]);
            if (ptr[5])
                pre2 = atol(ptr[5]);
            if (ii->netstat[0].rx_bytes >= pre1) {
                sum1 += ii->netstat[0].rx_bytes - pre1;
                sum2 += ii->netstat[0].tx_bytes - pre2;
            }
            else {
                /* just started or rebooted */
                sum1 += ii->netstat[0].rx_bytes;
                sum2 += ii->netstat[0].tx_bytes;
            } 
            snprintf(s_key, 128, "key = '%s:%d:%ld:%ld:%ld:%ld' ", 
                                 ptr[0]?ptr[0]:"",
                                 ii->gport == -1?gport:ii->gport,
                                 sum1, ii->netstat[0].rx_bytes,
                                 sum2, ii->netstat[0].tx_bytes);
            if (savestr)
                free(savestr);
        }
        if (ii && ii->ip && ii->ip[0] != '\0' && ii->ip[0] != ' ') {
            char * s = PQgetvalue(res, 0, 1);
            if (s == NULL || strlen(s) == 0 || strcmp(ii->ip, s))
                snprintf(s_ip, 100, "ip = '%s',", ii->ip);
        }
        if (node_id >= 0) {
            char * s = PQgetvalue(res, 0, 2);
            if (node_id == 0)
                snprintf(s_node_id, 20, "node_id = NULL,");
            else if (s == NULL || strlen(s) == 0 || node_id != atoi(s))
                snprintf(s_node_id, 20, "node_id = %d,", node_id);
        }
        if (ii && ii->status != DOMAIN_S_UNKNOWN) {
            char * s = PQgetvalue(res, 0, 3);
            if (s == NULL || strlen(s) == 0 || ii->status != atoi(s))
                snprintf(s_status, 20, "status = %d,", ii->status);
        }
    }
    PQclear(res);

    if (s_ip[0] == '\0' && s_status[0] == '\0' && s_node_id[0] == '\0' && s_key[0] == '\0')
        return 0;

    if (snprintf(sql, LINE_MAX, "UPDATE instance SET %s %s %s %s "
                                "%s "
                                "WHERE status != %d and id = %d;",
                                s_ip, s_status, s_node_id, s_key,
                                s_ip[0] == '\0' && s_status[0] == '\0' && s_node_id[0] == '\0' ? "" : 
                                    s_key[0] == '\0' ? " updated = 'now' " : ", updated = 'now' ",
                                DOMAIN_S_DELETE, instance_id) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
 
    return __db_exec(sql);
}

int db_instance_delete(int instance_id)
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX, "DELETE from instance WHERE id = %d "
                                "and status = %d;", 
                                instance_id, DOMAIN_S_DELETE) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return __db_exec(sql);
}

int db_node_instance_control_get(NodeCtrlInstance * ci, int * node_id)
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX,
                 "SELECT instance.name, instance.cpus, instance.memory, "
                 "instance.ip, instance.node_id, "
                 "instance.appliance_id, appliance.name, "
                 "appliance.checksum, instance.status, instance.key, "
                 "instance.config "
                 "from instance, appliance "
                 "where instance.id = %d and "
                 "appliance.id = instance.appliance_id;",
                 ci->ins_id) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;

    int ret = PQntuples(res);
    if (ret == 1) {
        char * s = PQgetvalue(res, 0, 0);
        if (s && strlen(s))
            ci->ins_name = strdup(s);
        ci->ins_vcpu = atoi(PQgetvalue(res, 0, 1));
        ci->ins_mem = atoi(PQgetvalue(res, 0, 2));
        if (ci->ins_mem > 131072)
            ci->ins_mem = 131072; /* 128G max */
        ci->ins_mem = ci->ins_mem << 10;
        s = PQgetvalue(res, 0, 3);
        if (s && strlen(s))
            ci->ins_ip = strdup(s);
        ci->ins_mac = NULL;
        *node_id = atoi(PQgetvalue(res, 0, 4));
        ci->app_id = atoi(PQgetvalue(res, 0, 5));
        s = PQgetvalue(res, 0, 6);
        if (s && strlen(s))
            ci->app_name = strdup(s);
        ci->app_checksum = malloc(33);
        if (ci->app_checksum)
            strncpy(ci->app_checksum, PQgetvalue(res, 0, 7), 32);
        ci->app_checksum[32] = 0;
        ci->ins_status = atoi(PQgetvalue(res, 0, 8));
        s = PQgetvalue(res, 0, 9);
        if (s && strlen(s)) {
            char * str, * str1;
            str = strdup(s);
            str1 = strtok(str, ":");
            if (str1)
                ci->osm_secret = strdup(str1);
            free(str);
        }
        ci->osm_tag = ci->ins_id;
        s = PQgetvalue(res, 0, 10);
        if (s && strlen(s))
            ci->osm_json = strdup(s);
        char ins_domain[21];
        if (g_c->vm_name_prefix == NULL)
            snprintf(ins_domain, 20, "i-%d", ci->ins_id);
        else
            snprintf(ins_domain, 20, "%s%d", g_c->vm_name_prefix, ci->ins_id);
        ci->ins_domain = strdup(ins_domain);
        ret = 0;
    }
    else if (ret > 1) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        ret = -1;
    }
    else {
        logerror(_("no record for instance %d in db\n"), ci->ins_id);
        ret = -1;
    }

    PQclear(res);
    return ret;
}

int db_instance_find_ip_by_status(int status, char * ins_ip[], int size)
{
    char sql[LINE_MAX];
    int ret = snprintf(sql, LINE_MAX,
                       "SELECT ip from instance where status = %d;",
                       status);
    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;

    ret = PQntuples(res);
    int i, j;
    for (i = j = 0; i< ret; i++) {
        char * s = PQgetvalue(res, i, 0);
        if (s && strlen(s) && strcmp(s, "0.0.0.0")) {
            if (j < size)
                ins_ip[j] = strdup(s);
            j++;
        }
    }

    PQclear(res);
    return j;
}

int db_instance_get_node(int id)
{
    char sql[LINE_MAX];
    int ret = snprintf(sql, LINE_MAX,
                       "SELECT node_id from instance where id = %d;",
                       id);
    if (ret >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return -1;

    ret = PQntuples(res);
    if (ret > 0)
        ret = atoi(PQgetvalue(res, 0, 0));

    PQclear(res);
    return ret;
}

int * db_instance_get_all(int * num, int status)
{
    int ret = -1;
    int * ids = NULL;

    if (num == NULL)
        return NULL;
    *num = -1;

    char s_status[100];
    if (status < 0)
        s_status[0] = '\0';
    else if (status == DOMAIN_S_START)
        snprintf(s_status, 100, "where status <= %d and status >= %d", DOMAIN_S_SERVING, DOMAIN_S_START);
    else
        snprintf(s_status, 100, "where status = %d", status);
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX, "SELECT id from instance %s;", s_status) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return NULL;
    }

    PGresult *res = __db_select(sql);
    if (res == NULL)
        return NULL;

    ret = PQntuples(res);
    if (ret <= 0)
        goto out;

    if (*num > 0)
        ret = ret > (*num) ? (*num) : ret;

    ids =  malloc(ret * sizeof(int));
    if (ids == NULL)
        goto out;

    int i;
    for (i = 0; i < ret; i++) {
        ids[i] = atoi(PQgetvalue(res, i, 0));
    }

out:
    *num = ret;
    PQclear(res);
    return ids;
}

int db_instance_init_status()
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX, "UPDATE instance SET status = %d "
                                "where status >= %d and status <= %d;",
                                DOMAIN_S_NEED_QUERY,
                                DOMAIN_S_START,
                                DOMAIN_S_SERVING) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return __db_exec(sql);
}

int db_node_init_status()
{
    char sql[LINE_MAX];
    if (snprintf(sql, LINE_MAX, "UPDATE node SET status = %d "
                                "where status >= %d and status <= %d;",
                                NODE_STATUS_OFFLINE,
                                NODE_STATUS_INITIALIZED,
                                NODE_STATUS_REGISTERED) >= LINE_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return __db_exec(sql);
}


int ly_db_init(void)
{
    char conninfo[LINE_MAX];

    sprintf(conninfo, "dbname=%s user=%s password=%s",
            g_c->db_name, g_c->db_user, g_c->db_pass);

    _db_conn = PQconnectdb(conninfo);

    if (PQstatus(_db_conn) == CONNECTION_BAD) {
        logerror(_("unable to connect to the database: %s\n"),
                    PQerrorMessage(_db_conn));
        return -1;
    }

    pthread_mutex_init(&_db_lock, NULL);
    return 0;
}

void ly_db_close(void)
{
    if (_db_conn)
        PQfinish(_db_conn);
}

int ly_db_check(void)
{
    char conninfo[LINE_MAX];

    sprintf(conninfo, "dbname=%s user=%s password=%s",
            g_c->db_name, g_c->db_user, g_c->db_pass);

    PGconn * conn = PQconnectdb(conninfo);

    if (PQstatus(conn) == CONNECTION_BAD) {
        logerror(_("unable to connect to the database: %s\n"),
                    PQerrorMessage(conn));
        return -1;
    }

    PQfinish(conn);
    return 0;
}

