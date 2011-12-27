#ifndef __LUOYUN_INCLUDE_CONTROL_node_manager_H
#define __LUOYUN_INCLUDE_CONTROL_node_manager_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <pthread.h>
#include "util/misc.h"
#include "util/luoyun.h"
#include "lyclc.h"


int node_queue_init(ComputeNodeQueue *qp);
int print_node_queue(ComputeNodeQueue *qp);

int get_node_queue (LyDBConn *db, ComputeNodeQueue *qp);
int put_node_queue (LyDBConn *db, ComputeNodeQueue *qp);


int node_register( LyDBConn *db,
                   ComputeNodeQueue *qp,
                   ComputeNodeItem *nitem );
int node_remove2(LyDBConn *db, ComputeNodeQueue *qp,
                 int S /* socket fd */);

int get_node_id_by_sfd(ComputeNodeQueue *qp, int sfd);


/* Following function have not use now */
int node_insert(ComputeNodeQueue *qp, ComputeNodeItem *np);
int node_append(ComputeNodeQueue *qp, ComputeNodeItem *np);
int node_remove(ComputeNodeQueue *qp, ComputeNodeItem *np);

// TODO: ugly find
ComputeNodeItem *find_node (ComputeNodeQueue *qp);


#endif /* __LUOYUN_INCLUDE_CONTROL_node_manager_H */
