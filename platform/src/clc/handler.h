#ifndef __LUOYUN_INCLUDE_control_handler_H
#define __LUOYUN_INCLUDE_control_handler_H

#include "control/job_manager.h"
#include "control/node_manager.h"
#include "control/instance_manager.h"
#include "lyclc.h"


int hl_node_register(LyDBConn *db, ComputeNodeQueue *qp,
                     LyRequest *request,
                     int efd, int S /* keep alive socket */);

int hl_instance_register(LyDBConn *db, LyInstanceQueue *qp,
                         LyRequest *request,
                         int efd, int S /* connect socket */);
int hl_instance_delete(LyDBConn *db, int S);

int hl_new_job(LyDBConn *db, JobQueue *qp,
               int S, /* socket */
               int datalen /* request data length */);


// old func
int hl_node_status ( LySockRequestHandler *RH,
                     ComputeNodeQueue *qp );
int hl_domain_status ( LyDBConn *db,
                       LySockRequestHandler *RH,
                       JobQueue *qp );
int hl_get_image_info ( LyDBConn *db,
                        LySockRequestHandler *RH );

#endif /* __LUOYUN_INCLUDE_control_handler_H */
