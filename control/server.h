#ifndef __LUOYUN_INCLUDE_control_server_H
#define __LUOYUN_INCLUDE_control_server_H

#include "util/luoyun.h"

#include <libpq-fe.h>

typedef struct LyDBConn_t {
     PGconn *conn;
     pthread_mutex_t lock;
} LyDBConn;


typedef struct ComputeNodeItem_t {
     int n_id;                 /* node id in database */
     ComputeNodeInfo *n_info;  /* info of compute node */
     struct ComputeNodeItem_t *n_next;     /* next job */
     struct ComputeNodeItem_t *n_prev;     /* prev job */
} ComputeNodeItem;


/* queue */
#include <libpq-fe.h>
typedef struct ComputeNodeQueue_t {
     ComputeNodeItem *q_head;   /* The first job */
     ComputeNodeItem *q_tail;   /* The last job */
     int q_gflag;            /* DB->NodeQueue */
     int q_pflag;            /* DB<-NodeQueue */
     pthread_rwlock_t q_lock;   /* lock */
} ComputeNodeQueue;


/* Job */
#include <pthread.h>

typedef enum JobStatus_t {
     JOB_S_UNKNOWN = 0,
     JOB_S_PREPARE = 1,
     JOB_S_RUNNING = 2,
     JOB_S_FINISHED = 3,
     JOB_S_FAILED = 4,
     JOB_S_CANCLED = 5,
     JOB_S_PENDING = 10,
     JOB_S_TIMEOUT = 11,
} JobStatus;

typedef enum JobTarget_t {
     JOB_TARGET_UNKNOWN = 0,
     JOB_TARGET_NODE = 1,
     JOB_TARGET_DOMAIN =2,
} JobTarget;


typedef enum JobAction_t {
     JOB_ACTION_UNKNOWN = 0,
     JOB_ACTION_RUN = 1,
     JOB_ACTION_STOP = 2,
     JOB_ACTION_SUSPEND = 3,
     JOB_ACTION_SAVE = 4,
     JOB_ACTION_REBOOT = 5,
} JobAction;

typedef struct Job_t {
     int j_id;                 /* id in database */
     JobStatus j_status;       /* status of this job */

     time_t j_created;         /* created time */
     time_t j_started;         /* started time */
     time_t j_ended;           /* ended time */

     JobTarget j_target_type;
     int j_target_id;

     JobAction j_action;

     //LySockHead *j_sockhead;
     pthread_t j_tid;          /* thread id of job */
     //int j_socket;             /* the socket from connect */
     struct Job_t *j_next;     /* next job */
     struct Job_t *j_prev;     /* prev job */
} Job;

/* queue */
#include <libpq-fe.h>
typedef struct JobQueue_t {
     Job *q_head;   /* The first job */
     Job *q_tail;   /* The last job */
     int q_count;          /* jobs number */
     int q_gflag;          /* get flag */
     int q_pflag;          /* put flag */
     pthread_rwlock_t q_lock; /* lock */
} JobQueue;


#endif /* __LUOYUN_INCLUDE_control_server_H */
