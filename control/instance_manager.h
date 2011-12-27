#ifndef __LUOYUN_INCLUDE_CONTROL_instance_manager_H
#define __LUOYUN_INCLUDE_CONTROL_instance_manager_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include "control/lyclc.h"
#include "util/luoyun.h"


typedef struct LyInstance_t {
     int id;
     int sfd;
     DomainInfo di;
     struct LyInstance_t *next;
     struct LyInstance_t *prev;
} LyInstance;


#include <pthread.h>
typedef struct LyInstanceQueue_t {
     LyInstance *head;   /* The first Instance */
     LyInstance *tail;   /* The last Instance */
     pthread_rwlock_t lock; /* lock */
} LyInstanceQueue;


int instance_queue_init(LyInstanceQueue *qp);

int instance_register(LyDBConn *db, LyInstanceQueue *qp, LyInstance *ins);
int instance_remove(LyDBConn *db, LyInstanceQueue *qp,  int sfd);

int get_instance_id_by_sfd(LyInstanceQueue *qp, int sfd);

int print_instance_queue(LyInstanceQueue *qp);

#endif /* __LUOYUN_INCLUDE_CONTROL_instance_manager_H */
