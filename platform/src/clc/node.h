#ifndef __LY_INCLUDE_CLC_NODE_H
#define __LY_INCLUDE_CLC_NODE_H

#define NODE_SCHEDULE_CPU_LIMIT(n) (n<<2)
#define NODE_SCHEDULE_MEM_LIMIT(m) (m<<1)

int node_schedule(void);

#endif
