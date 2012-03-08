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
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <errno.h>

#include "luoyun.h"
#include "logging.h"
#include "lyutil.h"

#include "../src/clc/lyjob.h"

PGconn * _db_conn = NULL;

int ly_db_init(void)
{
    printf("connect db\n");

    char conninfo[LINE_MAX];

    sprintf(conninfo, "dbname=%s user=%s password=%s",
            "luoyun", "luoyun", "luoyun");

    _db_conn = PQconnectdb(conninfo);

    if (PQstatus(_db_conn) == CONNECTION_BAD) {
        logerror(_("unable to connect to the database: %s\n"),
                 PQerrorMessage(_db_conn));
        return -1;
    }

    return 0;
}

void ly_db_close(void)
{
    printf("disconnect db\n");
    PQfinish(_db_conn);
}

static PGresult * __db_select(char *sql)
{
    PGresult *res;
    res = PQexec(_db_conn, sql);
    if (PQresultStatus(res) != PGRES_TUPLES_OK) {
        logerror(_("db select failed: %s\n"), PQerrorMessage(_db_conn));
        PQclear(res);
        return NULL;
    }
    return res;
}

static int __db_exec(char *sql)
{
    PGresult *res;
    res = PQexec(_db_conn, sql);
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        logerror(_("db exec failed: %s\n"), PQerrorMessage(_db_conn));
        PQclear(res);
        return -1;
    }
    PQclear(res);
    return 0;
}

int query_node(int id)
{
    PGresult *res;
    char sql[1024];
    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_NODE, id,
                 LY_A_NODE_QUERY, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;

    snprintf(sql, 1024, "SELECT id from job where target_id = %d order by id desc;", id);
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    return job_id;
}

int query_node_result(int id)
{
    PGresult *res;
    char sql[1024];
    snprintf(sql, 1024, "SELECT status from node where id = %d;", id);
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    printf("Node info: status %s, memory %s, load %s\n",
           PQgetvalue(res, 0, 0),
           "unknown",
           "unknown");
    return 0;
}

int find_node_to_enable()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from node where isenable = False order by id desc;");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    int id = atoi(PQgetvalue(res, 0, 0));
    return id;
}

int setup_run_job_in_db(int id, int isenable)
{
    PGresult *res;
    char sql[1024];
    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_NODE, id,
                 isenable ? LY_A_CLC_ENABLE_NODE : LY_A_CLC_DISABLE_NODE,
                 JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;

    snprintf(sql, 1024, "SELECT id from job where target_id = %d order by id desc;", id);
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    return job_id;
}

int job_result(int id)
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT status from job where id = %d;", id);
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    int status = atoi(PQgetvalue(res, 0, 0));
    printf("job status = %d\n", status);
    return status;
}

int send_new_job_to_clc(int id)
{
    printf("test_job_id = %d\n", id);

    int d[3] = {PKT_TYPE_WEB_NEW_JOB_REQUEST, sizeof(int), 0};
    d[2] = id;

    char * clc_ip = "192.168.1.107";
    int clc_port = 1369;
    int sfd;
    sfd = lyutil_connect_to_host(clc_ip, clc_port);
    if (sfd <= 0) {
        printf("Connect to %s:%d failed.\n", clc_ip, clc_port);
        return -1;
    }
    write(sfd, d, 3*sizeof(int));
    close(sfd);
    printf("packet sent to %s(%d)\n", clc_ip, clc_port);
    return 0;
}

int main(int argc, char *argv[])
{
    int node_id = -1, isenable = 1;
    if (argc == 3) {
        if (strcmp(argv[1], "disable") == 0) {
            node_id = atoi(argv[2]);
            isenable = 0;
        }
    }
    if (argc != 1 && isenable) {
        printf("wrong argument\n");
        return -1;
    }

    ly_db_init();

    if (isenable) {
        node_id = find_node_to_enable();
        printf("node to enable, %d\n", node_id);
        if (node_id <= 0)
            return 0;
    }
    int job_id = setup_run_job_in_db(node_id, isenable);
    send_new_job_to_clc(job_id);
    int status = job_result(job_id);
    while (!JOB_IS_FINISHED(status)){
        status = job_result(job_id);
        printf("sleep 1\n");
        sleep(1);
    }

    if (isenable == 0) {
        printf("done\n");
        ly_db_close();
        return 0;
    }

    printf("query node\n");
    job_id = query_node(node_id);
    if (job_id > 0) {
        send_new_job_to_clc(job_id);
        status = job_result(job_id);
        while (status > 0 && !JOB_IS_FINISHED(status)){
            status = job_result(job_id);
            printf("sleep 1\n");
            sleep(1);
        }
        query_node_result(node_id);
    }

    ly_db_close();
    return 0;
}
