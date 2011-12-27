#ifndef __LUOYUN_INCLUDE_CONTROL_JOB_MANAGER_H
#define __LUOYUN_INCLUDE_CONTROL_JOB_MANAGER_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include "util/misc.h"
#include "util/luoyun.h"
#include "lyclc.h"


int get_job_queue (LyDBConn *db, JobQueue *qp);

// old func
int job_queue_init(JobQueue *qp);
void print_job_queue(JobQueue *qp);

int put_job_queue (LyDBConn *db, JobQueue *qp);
int job_dispatch ( LyDBConn *db,
                   ComputeNodeQueue *nqp,
                   JobQueue *jqp );

/* APUE2 11.6 : Queue and Job method */

void job_insert(JobQueue *qp, Job *jp);
void job_append(JobQueue *qp, Job *jp);
void job_remove(JobQueue *qp, Job *jp);
Job *job_find(JobQueue *qp, pthread_t tid);
Job *create_job(int sk, LySockHead *sh);



int job_run ( LyDBConn *db, ComputeNodeQueue *nqp,
              JobQueue *jqp, Job *jp );
int domain_job_run ( LyDBConn *db, ComputeNodeQueue *nqp,
                     JobQueue *jqp, Job *jp );

#endif /* __LUOYUN_INCLUDE_CONTROL_JOB_MANAGER_H */
