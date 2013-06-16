#ifndef __LY_INCLUDE_CLC_JOB_H
#define __LY_INCLUDE_CLC_JOB_H

#include "../util/list.h"

typedef struct LYJobInfo_t {
    struct list_head j_list;

     int j_id;                 /* id in database */
     int j_status;       /* status of this job */

     time_t j_created;         /* created time */
     time_t j_started;         /* started time */
     time_t j_ended;           /* old: ended time */
     time_t j_last_run;        /* last time the job runs */

     int j_target_type;
     int j_target_id;

     int j_action;

     int j_ent_id;             /* job process entity */
     int j_pending_nr;         /* > 0: the job pending number, 0: being processed, -1: not busy */
} LYJobInfo;

void job_print_queue();
int job_exist(LYJobInfo * job);
int job_check(LYJobInfo * job);
LYJobInfo * job_find(int id);
int job_insert(LYJobInfo * job);
int job_remove(LYJobInfo * job);
int job_update_status(LYJobInfo * job, int status);
int job_dispatch(void);
int job_init(void);
void job_cleanup(void);

/*
** in lyjob2.c
*/ 
#define CLC_JOB_QUERY_NODE_INTERVAL       3600
#define CLC_JOB_CLEANUP_NODE_INTERVAL     86400
#define CLC_JOB_QUERY_INSTANCE_INTERVAL   120
int job_internal_query_instance(int id);
int job_internal_dispatch(void);
int job_internal_init(void);

#endif

