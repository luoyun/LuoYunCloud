#ifndef __LUOYUN_INCLUDE_compute_handler_H
#define __LUOYUN_INCLUDE_compute_handler_H

#include <stdio.h>
#include <stdlib.h>

#include "util/misc.h"
#include "util/luoyun.h"
#include "compute/domain.h"
#include "util/download.h"


int hl_domain_control(CpConfig *C,
                      int S, /* socket */
                      int datalen /* request data length */);

#endif /* __LUOYUN_INCLUDE_compute_handler_H */
