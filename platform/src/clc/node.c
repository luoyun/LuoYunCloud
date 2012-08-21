/*
** Copyright (C) 2012 LuoYun Co. 
**
**           Authors:
**                    lijian.gnu@gmail.com 
**                    zengdongwu@hotmail.com
**  
** This program is free software; you can redistribute it and/or modify
** it under the terms of the GNU General Public License as published by
** the Free Software Foundation; either version 2 of the License, or
** (at your option) any later version.
**  
** This program is distributed in the hope that it will be useful,
** but WITHOUT ANY WARRANTY; without even the implied warranty of
** MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
** GNU General Public License for more details.
**  
** You should have received a copy of the GNU General Public License
** along with this program; if not, write to the Free Software
** Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
**  
*/
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "lyclc.h"
#include "entity.h"
#include "node.h"

int node_schedule()
{
    int ent_curr = -1;
    int ent_id = NODE_SCHEDULE_NODE_UNAVAIL;
    int cpu_avail_max = 0;
    while(1) {
        NodeInfo * ni = ly_entity_data_next(LY_ENTITY_NODE, &ent_curr);
        if (ni == NULL)
            break;
        if (!ly_entity_is_registered(ent_curr) ||
            !ly_entity_is_enabled(ent_curr))
            continue;

        if (ent_id < 0)
            ent_id = NODE_SCHEDULE_NODE_BUSY;
        if (ni->storage_free <= g_c->node_storage_low)
            continue;
        logdebug("%s:%d %d %d %d\n", __func__,
                  ni->cpu_commit,
                  NODE_SCHEDULE_CPU_LIMIT(ni->cpu_max),
                  ni->mem_commit,
                  NODE_SCHEDULE_MEM_LIMIT(ni->mem_max));
        if (ni->cpu_commit >= NODE_SCHEDULE_CPU_LIMIT(ni->cpu_max) ||
            ni->mem_commit >= NODE_SCHEDULE_MEM_LIMIT(ni->mem_max)) {
            continue;
        }
        int cpu_avail = NODE_SCHEDULE_CPU_LIMIT(ni->cpu_max) - ni->cpu_commit;
        if (cpu_avail > cpu_avail_max) {
            cpu_avail_max = cpu_avail;
            ent_id = ent_curr;
        }
    }
    return ent_id;
}

