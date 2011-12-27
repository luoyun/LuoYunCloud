#ifndef __LUOYUN_INCLUDE_CONTROL_client_manager_H
#define __LUOYUN_INCLUDE_CONTROL_client_manager_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include "control/lyclc.h"
#include "util/luoyun.h"



/* LuoYun Client Queue Struct */

typedef enum LyClientType_t {
     LY_CLIENT_IS_NODE = 1,
     LY_CLIENT_IS_INSTANCE = 2,
} LyClientType;

typedef struct LyClient_t {
     int               id;    /* id in DB */
     LyClientType      type;
     int               sfd;   /* client socket */
     struct LyClient_t *next;
     struct LyClient_t *prev;
} LyClient;

#include <pthread.h>
typedef struct LyClientQueue_t {
     LyClient *head;   /* The first Instance */
     LyClient *tail;   /* The last Instance */
     pthread_rwlock_t lock; /* lock */
} LyClientQueue;



int client_queue_init (LyClientQueue *qp);
int client_register(LyClientQueue *qp, int id, int type, int sfd);
int client_remove(LyClientQueue *qp, LyDBConn *db, int sfd);

#endif /* __LUOYUN_INCLUDE_CONTROL_client_manager_H */
