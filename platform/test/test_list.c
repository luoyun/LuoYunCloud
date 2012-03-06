/*
** Copyright (C) 2012 LuoYun Co. 
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
#include <stddef.h>
#include <unistd.h>
#include <sys/types.h>

#include "list.h"

void testlist(void)
{
    struct mylist {
        struct list_head node;
        int data;
    };

    //struct mylist listhead;
    //INIT_LIST_HEAD(&listhead.node);
    //listhead.data = -1;
    static LIST_HEAD(listhead);
    struct mylist *curr, *tmp;
    int i = 0;

    INIT_LIST_HEAD(&listhead);
    do {

        struct mylist *l = malloc(sizeof(struct mylist));
        if (!l) {
            printf("malloc failed %s %d\n", __FILE__, __LINE__);
            goto out;
        }
        l->data = i++;
        list_add(&(l->node), &(listhead));

    } while (i < 10);
    for (int t = 1; t < 10; t++)
        printf("%d\n", t);
    list_for_each_entry(curr, &(listhead), node) {
        if (curr)
            printf("%d ", curr->data);
    }
    printf("\n");

  out:
    list_for_each_entry_safe(curr, tmp, &(listhead), node) {
        printf("deleting %d\n", curr->data);
        list_del(&(curr->node));
        free(curr);
    }
    printf("\n");
    return;
}

int main()
{
    testlist();
    printf("This is test program for luoyun cloud program!\n");
    return (0);
}
