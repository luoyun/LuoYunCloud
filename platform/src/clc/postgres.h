#ifndef __LY_INCLUDE_CLC_POSTGRES_H
#define __LY_INCLUDE_CLC_POSTGRES_H

#include "../luoyun/luoyun.h"
#include "lyjob.h"

#define DB_NODE_FIND_BY_TAG  1
#define DB_NODE_FIND_BY_IP   2
#define DB_NODE_FIND_BY_ID   3

/* node info from db */
typedef struct DBNodeRegInfo_t {
    int id;
    int status;
    int tag;
    char * ip;
    char * secret;
    int enabled;
}DBNodeRegInfo;
int db_node_reginfo_free(DBNodeRegInfo * nf);

int db_node_exist(int type, void * data);
int db_node_find(int type, void * data, DBNodeRegInfo * db_nf);
int db_node_find_secret(int type, void * data, char ** secret);
int db_node_update_secret(int type, void * data, char * secret);
int db_node_update(int type, void * data, NodeInfo * nf);
int db_node_update_status(int type, void * data, int status);
int db_node_enable(int id, int enable);
int db_node_insert(NodeInfo *nf);
int db_node_instance_control_get(NodeCtrlInstance *ci, int *node_id);
int db_job_get(LYJobInfo * job);
int db_job_get_all(void);
int db_job_update_status(LYJobInfo * job);
int db_instance_find_secret(int id, char ** secret);
int db_instance_update_secret(int id, char * secret);
int db_instance_update_status(int instance_id, InstanceInfo * ii, int node_id);
int db_instance_find_ip_by_status(int status, char * ins_ip[], int size);
int db_instance_get_node(int id);
int db_instance_get_all(int **ids);
int db_instance_init_status();

int ly_db_init();
void ly_db_close();
int ly_db_check(void);

#endif
