#ifndef __LUOYUN_INCLUDE_compute_handler_H
#define __LUOYUN_INCLUDE_compute_handler_H

#include <stdio.h>
#include <stdlib.h>

#include "util/misc.h"
#include "util/luoyun.h"
#include "compute/domain.h"
#include "util/download.h"


typedef struct DomainControlHandler_t {
     LyComputeServerConfig *sc;
     int action;
     DomainInfo *dip;
} DomainControlHandler;


int hl_control_domain ( LyComputeServerConfig *sc,
                        LySockRequestHandler *RH );

#endif /* __LUOYUN_INCLUDE_compute_handler_H */
