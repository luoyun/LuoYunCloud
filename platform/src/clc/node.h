#ifndef __LY_INCLUDE_CLC_NODE_H
#define __LY_INCLUDE_CLC_NODE_H

#include "lyclc.h"

#define NODE_SCHEDULE_CPU_LIMIT(n) (n*g_c->node_cpu_factor)
#define NODE_SCHEDULE_MEM_LIMIT(m) (m*g_c->node_mem_factor)

#define NODE_SCHEDULE_NODE_BUSY         -2
#define NODE_SCHEDULE_NODE_UNAVAIL      -1
int node_schedule(void);

#endif
