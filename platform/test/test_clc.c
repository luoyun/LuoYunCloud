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
int ubantu_app_id = -1;
int ubantu_app_keep = 0;

int test_ins_id = -1;

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

int setup_applaince_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from appliance where name = 'rhel56n1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;

    if (PQntuples(res) > 0) {
        ubantu_app_keep = 1;
        printf("app rhel56n1 exists already.\n");
        PQclear(res);
        return 0;
    }

    if (snprintf(sql, 1024,
                 "INSERT INTO appliance (name, filesize, checksum, "
                 "created, updated) "
                 "VALUES ('%s', %d, '%s',"
                 "'now', 'now');",
                 "rhel56n1", 372803101, "6219855488130d275d7abb43db7467f9"
                 ) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    return __db_exec(sql);
}

int reset_applaince_in_db()
{
    if (ubantu_app_keep)
        return 0;
    char sql[1024];
    snprintf(sql, 1024, "delete from appliance where name = 'rhel56n1';");
    printf("%s\n", sql);
    return __db_exec(sql);
}

int setup_instance_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    if (PQntuples(res) > 0) {
        test_ins_id = atoi(PQgetvalue(res, 0, 0));
        printf("instance exists already, test_ins_id = %d\n", test_ins_id);
        PQclear(res);
        return 0;
    }

    snprintf(sql, 1024, "SELECT id from appliance where name = 'rhel56n1';");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    ubantu_app_id = atoi(PQgetvalue(res, 0, 0));
    printf("ubantu_app_id = %d\n", ubantu_app_id);
    PQclear(res);

    if (snprintf(sql, 1024,
                 "INSERT INTO instance (name, appliance_id, mac, "
                 "user_id, status, created, updated) "
                 "VALUES ('%s', %d, '%s',"
                 "1, %d, 'now', 'now');",
                 "testn1", ubantu_app_id, "00:16:36:50:6f:99",
                 DOMAIN_S_NEW) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    return __db_exec(sql);
}

int reset_instance_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "delete from instance where name = 'testn1';");
    printf("%s\n", sql);
    return __db_exec(sql);
}


int setup_run_job_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    test_ins_id = atoi(PQgetvalue(res, 0, 0));
    printf("test_ins_id = %d\n", test_ins_id);
    PQclear(res);

    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_INSTANCE, test_ins_id,
                 LY_A_NODE_RUN_INSTANCE, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;

    snprintf(sql, 1024, "SELECT id from job order by id desc;");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    PQclear(res);
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
    PQclear(res);
    return status;
}

int setup_stop_job_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    test_ins_id = atoi(PQgetvalue(res, 0, 0));
    printf("test_ins_id = %d\n", test_ins_id);
    PQclear(res);

    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_INSTANCE, test_ins_id,
                 LY_A_NODE_STOP_INSTANCE, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;
 
    snprintf(sql, 1024, "SELECT id from job order by id desc;");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    PQclear(res);
    return job_id;
}

int setup_reboot_job_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    test_ins_id = atoi(PQgetvalue(res, 0, 0));
    printf("test_ins_id = %d\n", test_ins_id);
    PQclear(res);

    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_INSTANCE, test_ins_id,
                 LY_A_NODE_REBOOT_INSTANCE, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;
 
    snprintf(sql, 1024, "SELECT id from job order by id desc;");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    PQclear(res);
    return job_id;
}

int setup_destroy_job_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    test_ins_id = atoi(PQgetvalue(res, 0, 0));
    printf("test_ins_id = %d\n", test_ins_id);
    PQclear(res);

    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_INSTANCE, test_ins_id,
                 LY_A_NODE_DESTROY_INSTANCE, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;

    snprintf(sql, 1024, "SELECT id from job order by id desc;");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    PQclear(res);
    return job_id;
}

int query_osm()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    test_ins_id = atoi(PQgetvalue(res, 0, 0));
    printf("test_ins_id = %d\n", test_ins_id);
    PQclear(res);

    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_INSTANCE, test_ins_id,
                 LY_A_OSM_QUERY, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;

    snprintf(sql, 1024, "SELECT id from job order by id desc;");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    PQclear(res);
    return job_id;
}

int query_instance()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    test_ins_id = atoi(PQgetvalue(res, 0, 0));
    printf("test_ins_id = %d\n", test_ins_id);
    PQclear(res);

    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_INSTANCE, test_ins_id,
                 LY_A_NODE_QUERY_INSTANCE, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;

    snprintf(sql, 1024, "SELECT id from job order by id desc;");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    PQclear(res);
    return job_id;
}

int query_instance_result()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT status from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    int status = atoi(PQgetvalue(res, 0, 0));
    printf("instance status from querying = %d\n", status);
    PQclear(res);

    return 0;
}

int query_node()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT node_id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    int node_id = atoi(PQgetvalue(res, 0, 0));
    printf("node id = %d\n", node_id);
    PQclear(res);
    if (node_id <= 0) {
        printf("node not valid\n");
        return -1;
    }

    if (snprintf(sql, 1024,
                 "INSERT INTO job (target_type, target_id, "
                 "user_id, action, status, created, started) "
                 "VALUES (%d, %d, "
                 "1, %d, %d, 'now', 'now');",
                 JOB_TARGET_NODE, node_id,
                 LY_A_NODE_QUERY, JOB_S_INITIATED) >= LINE_MAX) {
        printf("error in %s(%d)\n", __func__, __LINE__);
        return -1;
    }
    printf("%s\n", sql);
    if (__db_exec(sql) < 0)
        return -1;

    snprintf(sql, 1024, "SELECT id from job order by id desc;");
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    int job_id = atoi(PQgetvalue(res, 0, 0));
    printf("job id = %d\n", job_id);
    PQclear(res);
    return job_id;
}

int query_node_result()
{
    char sql[1024];
    snprintf(sql, 1024, "SELECT node_id from instance where name = 'testn1';");
    PGresult * res = __db_select(sql);
    if (res == NULL)
        return -1;
    int node_id = atoi(PQgetvalue(res, 0, 0));
    PQclear(res);

    snprintf(sql, 1024, "SELECT status from node where id = %d;", node_id);
    res = __db_select(sql);
    if (res == NULL)
        return -1;
    printf("Node info: status %s, memory %s, load %s\n",
           PQgetvalue(res, 0, 0),
           "unknown",
           "unknown");
    PQclear(res);
    return 0;
}

int reset_job_in_db()
{
    char sql[1024];
    snprintf(sql, 1024, "delete from job where target_id = %d;", test_ins_id);
    printf("%s\n", sql);
    return __db_exec(sql);
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

int echo_test_to_clc()
{
    printf("echo test\n");

    char * s = "hahahahahahahaha";
    int len = strlen(s);

    char * clc_ip = "192.168.1.107";
    int clc_port = 1369;
    int sfd;
    sfd = lyutil_connect_to_host(clc_ip, clc_port);
    if (sfd <= 0) {
        printf("Connect to %s:%d failed.\n", clc_ip, clc_port);
        return -1;
    }
    printf("%s\n", s);
    if (ly_packet_send(sfd, PKT_TYPE_TEST_ECHO_REQUEST, s, len) < 0) {
        printf("echo failed\n");
        close(sfd);
        return -1;
    }
    char r[100];
    int l;
    do {
        l = read(sfd, r, 100);
    } while(l == -1 && errno == EAGAIN);
    printf("%d %d\n", *(int *)r, *((int *)r + 1));
    if (l != len + 8)
        printf("echo failed\n");
    if (l > 0) {
        r[l] = 0;
        printf("%s\n", r+8);
        if (strcmp(s, r+8) == 0)
            printf("echo worked\n");
        else
            printf("echo failed\n");
    }
    else
        perror(NULL);
    close(sfd);
    return 0;
}

enum {
   ALL,
   Q_INS,
   Q_OSM,
   Q_NODE,
   START,
   STOP,
   DESTROY,
   REBOOT,
   ECHO,
   SHELL,
};

int main(int argc, char * argv[])
{
    int cmd;
    if (argc == 1)
        cmd = ALL;
    else if (argc == 2) {
        if (strcmp(argv[1], "start") == 0)
            cmd = START;
        else if (strcmp(argv[1], "stop") == 0)
            cmd = STOP;
        else if (strcmp(argv[1], "destroy") == 0)
            cmd = DESTROY;
        else if (strcmp(argv[1], "reboot") == 0)
            cmd = REBOOT;
        else if (strcmp(argv[1], "shell") == 0)
            cmd = SHELL;
        else 
            cmd = ECHO;
    }
    else if (argc == 3) {
        if (strncmp(argv[2], "instance", 3) == 0)
            cmd = Q_INS;
        else if (strncmp(argv[2], "osm", 3) == 0)
            cmd = Q_OSM;
        else
            cmd = Q_NODE;
    }
    else 
        return 0;
 
    if (cmd == ALL || cmd == ECHO)
        echo_test_to_clc();

    if (cmd == ECHO)
        return 0;

    ly_db_init();
    setup_applaince_in_db();
    setup_instance_in_db();

    int id, status;
    if (cmd == SHELL) {
        printf("type command, s|o|r|d|x|i/m/n/|I/N\n");
        char c = '\0';
        printf("cmd> ");
        while( c != 'x') {
            scanf("%1c", &c);
            if (c == 's')
                id = setup_run_job_in_db();
            else if (c == 'o')
                id = setup_stop_job_in_db();
            else if (c == 'r')
                id = setup_reboot_job_in_db();
            else if (c == 'd')
                id = setup_destroy_job_in_db();
            else if (c == 'i')
                id = query_instance();
            else if (c == 'm')
                id = query_osm();
            else if (c == 'n')
                id = query_node();
            else if (c == 'I') {
                id = query_instance_result();
                continue;
            }
            else if (c == 'N') {
                id = query_node_result();
                continue;
            }
            else if (c == 't') {
                job_result(id);
                continue;
            }
            else if (c == 'x')
                break;
            else if (c == '\n') {
                printf("cmd> ");
                continue;
            }
            else {
                printf("\nunknow command...<%c>\n", c);
                printf("type command, s|o|r|d|x|i/m/n/|I/N\n");
                continue;
            }
            if (id <= 0) {
                printf("invalide job id %d\n", id);
                continue;
            }
            send_new_job_to_clc(id);
            job_result(id);
        }
    }
      

    if (cmd == ALL || cmd == START) {
        printf("run instance\n");
        id = setup_run_job_in_db();
        send_new_job_to_clc(id);
        status = job_result(id);
        while (!JOB_IS_FINISHED(status)){
            status = job_result(id);
            printf("sleep 1\n");
            sleep(1);
        }
    }

    if (cmd == ALL || cmd == START || cmd == Q_INS) {
        printf("query instance\n");
        id = query_instance();
        send_new_job_to_clc(id);
        status = job_result(id);
        while (!JOB_IS_FINISHED(status)){
            status = job_result(id);
            printf("sleep 1\n");
            sleep(1);
        }
        query_instance_result();
    }

    if (cmd == ALL || cmd == START || cmd == Q_OSM) {
        printf("query osm\n");
        id = query_osm();
        send_new_job_to_clc(id);
        status = job_result(id);
        while (!JOB_IS_FINISHED(status)){
            status = job_result(id);
            printf("sleep 1\n");
            sleep(1);
        }
        query_instance_result();
    }

    if (cmd == ALL || cmd == START || cmd == Q_NODE) {
         printf("query node\n");
         id = query_node();
         if (id > 0) {
             send_new_job_to_clc(id);
             status = job_result(id);
             while (status > 0 && !JOB_IS_FINISHED(status)){
                 status = job_result(id);
                 printf("sleep 1\n");
                 sleep(1);
             }
             query_node_result();
        }
    }

    if (cmd == ALL) {
        printf("sleep 20 seconds\n");
        sleep(20);
    }

    if (cmd == ALL || cmd == STOP) {
        printf("stop instance\n");
        id = setup_stop_job_in_db();
        send_new_job_to_clc(id);
        status = job_result(id);
        while (!JOB_IS_FINISHED(status)){
            status = job_result(id);
            printf("sleep 1\n");
            sleep(1);
        }
    }

    if (cmd == REBOOT) {
        printf("reboot instance\n");
        id = setup_reboot_job_in_db();
        send_new_job_to_clc(id);
        status = job_result(id);
        while (!JOB_IS_FINISHED(status)){
            status = job_result(id);
            printf("sleep 1\n");
            sleep(1);
        }
    }

    if (cmd == ALL) {
        printf("sleep 30 seconds\n");
        sleep(30);
    }

    if (cmd == ALL || cmd == DESTROY) {
        printf("destroy instance\n");
        id = setup_destroy_job_in_db();
        send_new_job_to_clc(id);
        status = job_result(id);
        while (!JOB_IS_FINISHED(status)){
            status = job_result(id);
            printf("sleep 1\n");
            sleep(1);
        }
    }

    if (cmd == ALL) {
        printf("sleep 20 seconds before cleanning up database\n");
        sleep(20);
        reset_job_in_db();

        reset_instance_in_db();
        reset_applaince_in_db();
    }

    ly_db_close();
    return 0;
}
