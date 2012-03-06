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

#include "path_utils.h"
#include "lyutil.h"

void testcreatepidfile(char *name)
{
    int ret;

    lyutil_remove_pid_file(".", name);
    ret = lyutil_create_pid_file(".", name);
    if (ret != 0) {
        printf("testcreatepidfile (pid file creating) failed!\n");
        return;
    }

    ret = lyutil_create_pid_file(".", name);
    if (ret != 1) {
        printf("testcreatepidfile (pid file reading) failed!\n");
        return;
    }

    lyutil_remove_pid_file(".", name);
    printf("testcreatepidfile passed!\n");
    return;
}

int main(int argc, char **argv)
{
    char name[40];
    get_basename(name, 40, argv[0]);
    testcreatepidfile(name);
    printf("This is test program for luoyun cloud program!\n");
    return (0);
}
