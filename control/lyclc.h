#ifndef __LUOYUN_INCLUDE_control_lyclc_H
#define __LUOYUN_INCLUDE_control_lyclc_H

#include <pthread.h>
#include "util/luoyun.h"


#define PROGRAM_NAME "lyclc"
#define PROGRAM_VERSION "0.1"

#define DEFAULT_CONFIG_PATH "/etc/LuoYun/lyclc.conf"
#define DEFAULT_LOG_PATH "/var/log/lyclc.log"





#include <libpq-fe.h>

typedef struct LyDBConn_t {
     PGconn *conn;
     pthread_mutex_t lock;
} LyDBConn;


typedef struct ComputeNodeItem_t {
     int id;   /* ID in DB */
     int sfd;  /* socket for keep alive */
     time_t updated;
     ComputeNodeInfo node;  /* info of compute node */
     struct ComputeNodeItem_t *n_next;     /* next node */
     struct ComputeNodeItem_t *n_prev;     /* prev node */
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
     JOB_S_QUERYING = 12,
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

#define DEFAULT_JOB_TIMEOUT 1200
#define NODE_JOB_TIMEOUT 1200
#define DOMAIN_JOB_TIMEOUT 1200

typedef struct Job_t {
     int j_id;                 /* id in database */
     JobStatus j_status;       /* status of this job */

     time_t j_created;         /* created time */
     time_t j_started;         /* started time */
     time_t j_ended;           /* old: ended time */

     JobTarget j_target_type;
     int j_target_id;

     JobAction j_action;

     //LySockHead *j_sockhead;
     pthread_t j_tid;          /* thread id of job */
     int j_sfd;                /* the socket from connect */
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


#endif /* __LUOYUN_INCLUDE_control_lyclc_H */
