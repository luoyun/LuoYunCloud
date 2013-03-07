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

int node_schedule(int node_id)
{
    if (g_c->node_select == NODE_SELECT_LAST_ONLY && node_id > 0) {
        int ent_id = ly_entity_find_by_db(LY_ENTITY_NODE, node_id);
        if (!ly_entity_is_registered(ent_id) || !ly_entity_is_enabled(ent_id))
            return NODE_SCHEDULE_NODE_UNAVAIL;

        LYNodeData * nd = ly_entity_data(ent_id);
        if (nd == NULL)
            return NODE_SCHEDULE_NODE_UNAVAIL;

        if (nd->ins_job_busy_nr >= g_c->node_ins_job_busy_limit)
            return NODE_SCHEDULE_NODE_STROKE;

        NodeInfo * nf = &nd->node;
        if (nf->status == NODE_STATUS_BUSY || nf->status == NODE_STATUS_ERROR) {
            logwarn(_("node %d is %s\n"), node_id,
                      nf->status == NODE_STATUS_BUSY ?  "busy" : "in error state");
            return NODE_SCHEDULE_NODE_BUSY;
        }

        if (nf->cpu_commit >= nf->cpu_vlimit || nf->mem_commit >= nf->mem_vlimit)
            return NODE_SCHEDULE_NODE_BUSY;

        return ent_id;
    }

    int ent_curr = -1;
    int ent_id = NODE_SCHEDULE_NODE_UNAVAIL;
    int cpu_avail_max = 0;
    while(1) {
        LYNodeData * nd = ly_entity_data_next(LY_ENTITY_NODE, &ent_curr);
        if (nd == NULL)
            break;
        if (!ly_entity_is_registered(ent_curr) ||
            !ly_entity_is_enabled(ent_curr))
            continue;

        if (ent_id == NODE_SCHEDULE_NODE_UNAVAIL)
            ent_id = NODE_SCHEDULE_NODE_BUSY;

        NodeInfo * nf = &nd->node;
        if (nf->storage_free <= g_c->node_storage_low) {
            logwarn(_("node %d storage is low.\n"), ly_entity_db_id(ent_curr));
            continue;
        }

        logdebug("%s:%d %d %d %d\n", __func__,
                  nf->cpu_commit, nf->cpu_vlimit,
                  nf->mem_commit, nf->mem_vlimit);

        if (nf->cpu_commit >= nf->cpu_vlimit || nf->mem_commit >= nf->mem_vlimit) {
            logwarn(_("node %d is busy.\n"), ly_entity_db_id(ent_curr));
            continue;
        }

        if (nd->ins_job_busy_nr >= g_c->node_ins_job_busy_limit) {
            if (ent_id == NODE_SCHEDULE_NODE_BUSY)
                ent_id = NODE_SCHEDULE_NODE_STROKE;
            logwarn(_("node %d is stroking.\n"), ly_entity_db_id(ent_curr));
            continue;
        }

        int cpu_avail = nf->cpu_vlimit - nf->cpu_commit;
        if (cpu_avail > cpu_avail_max) {
            cpu_avail_max = cpu_avail;
            ent_id = ent_curr;
        }
    }
    return ent_id;
}

