#ifndef __LY_INCLUDE_CLC_NODE_H
#define __LY_INCLUDE_CLC_NODE_H

#include "lyclc.h"

typedef struct LYNodeData_t {
    int ins_job_busy_nr;
    NodeInfo node;
} LYNodeData;

#define NODE_SCHEDULE_NODE_STROKE       -3
#define NODE_SCHEDULE_NODE_BUSY         -2
#define NODE_SCHEDULE_NODE_UNAVAIL      -1
int node_schedule(int node_id);

#endif
