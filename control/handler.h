#ifndef __LUOYUN_INCLUDE_control_handler_H
#define __LUOYUN_INCLUDE_control_handler_H

#include "control/job_manager.h"
#include "control/node_manager.h"
#include "control/server.h"

int hl_new_job ( LyDBConn *db,
                 LySockRequestHandler *RH,
                 JobQueue *jp);
int hl_node_status ( LySockRequestHandler *RH,
                     ComputeNodeQueue *qp );
int hl_domain_status ( LyDBConn *db,
                       LySockRequestHandler *RH,
                       JobQueue *qp );
int hl_get_image_info ( LyDBConn *db,
                        LySockRequestHandler *RH );

#endif /* __LUOYUN_INCLUDE_control_handler_H */
