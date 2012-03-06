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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>             /* strlen, strcpy */
#include <sys/types.h>          /* open */
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>             /* read, close */
#include <limits.h>             /* LINE_MAX etc */
#include <errno.h>              /* errno */
#include <utime.h>              /* utime */

#include "osmmisc.h"

/* filter the white space in str. eg ' ', '\t', comment . */
int str_filter_white_space(char *str)
{
    int i, j;
    int length = strlen(str);
    char newstr[LINE_MAX] = { '\0' };

    for (i = 0, j = 0; i < length; i++)
        if (str[i] != ' ' && str[i] != '\t' && str[i] != '\n')
            newstr[j++] = str[i];

    if ((*newstr == '#') || (*newstr == ';'))
        *newstr = '\0';

    newstr[j] = '\0';
    strcpy(str, newstr);

    return 0;
}

/* "touch" a file, creating if necessary */
int touch(const char *path)
{
    int fd = open(path, O_WRONLY | O_CREAT | O_NONBLOCK, 0644);
    if (fd >= 0) {
        close(fd);
        if (utime(path, NULL) != 0)
            return 1;
    }
    return 0;
}

