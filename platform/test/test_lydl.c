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

#include "download.h"

void testdl(void)
{
    char tmpfile[20];
    int fd;

    sprintf(tmpfile, "tmpfile.XXXXXX");
    fd = mkstemp(tmpfile);
    if (fd == -1) {
        printf("failed create tmpfile\n");
        return;
    }
    if (lyutil_download("http://localhost:8080/index.html", tmpfile))
        printf("test ly_dl failed\n");
    else
        printf("test ly_dl passed\n");

    /* remove tmpfile */
    close(fd);
    unlink(tmpfile);
    return;
}

int main()
{
    testdl();
    printf("This is test program for luoyun cloud program!\n");
    return (0);
}
