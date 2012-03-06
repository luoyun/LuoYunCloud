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
#include "entity.h"
#include "node.h"

int node_schedule()
{
    int ent_curr = -1;
    unsigned int mem = 0;
    int ent_id = -1;
    while(1) {
        NodeInfo * ni = ly_entity_data_next(LY_ENTITY_NODE, &ent_curr);
        if (ni == NULL)
            break;
        if (!ly_entity_is_registered(ent_curr))
            continue;
        if (ni->free_memory > mem) {
            mem = ni->free_memory;
            ent_id = ent_curr;
        }
    }
    return ent_id;
}

