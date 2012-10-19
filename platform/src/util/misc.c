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
#include <string.h>             /* strlen, strcpy */
#include <sys/types.h>          /* open */
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>             /* read, close */
#include <limits.h>             /* LINE_MAX etc */
#include <errno.h>              /* errno */
#include <utime.h>              /* utime */

#include "logging.h"
#include "misc.h"

#define BUFSIZE 1024

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

/* check whether file not exist, 1: not exist, 0: exist */
int file_not_exist(char *file)
{
    int rc;
    struct stat mystat;

    if (!file) {
        return (1);
    }

    rc = lstat(file, &mystat);
    if (rc < 0 || !S_ISREG(mystat.st_mode)) {
        return (1);
    }
    return (0);
}

/*
** read file content into a string
** calling function should free the string after being used
*/
char *fp2str(FILE * fp, int size)
{
#define INCREMENT 512
    int buf_max = size <= 0 || size > INCREMENT ? INCREMENT : size;
    int buf_current = 0;
    char *last_read;
    char *buf = NULL;

    if (fp == NULL)
        return NULL;
    do {
        /* create/enlarge the buffer */
        void *new_buf;
        if ((new_buf = realloc(buf, buf_max)) == NULL) {
            if (buf != NULL) {  /* previous realloc()s worked */
                free(buf);      /* free partial buffer */
            }
            return NULL;
        }
        buf = new_buf;
        logdebug(_("fp2str: enlarged buf to %d\n"), buf_max);

        do {                    /* read in until EOF or buffer is full */
            last_read =
                fgets(buf + buf_current, buf_max - buf_current, fp);
            if (last_read != NULL)
                buf_current = strlen(buf);
            logdebug(_("fp2str: read %d characters so far (max=%d, last=%s)\n"),
                       buf_current, buf_max, last_read ? "no" : "yes");
        } while (last_read && buf_max > buf_current + 1);       /* +1 is needed for fgets() to put \0 */

        if (size <= 0)
            buf_max += INCREMENT;   /* in case it is full */
        else if (buf_max >= size)
            break;
        else if (buf_max + INCREMENT > size)
            buf_max = size;
        else
            buf_max += INCREMENT;
    } while (last_read);

    if (buf_current < 1) {
        free(buf);
        buf = NULL;
    }

    return buf;
}

/* read file 'path' into a new string */
char *file2str(const char *path, int size)
{
    char *content = NULL;
    int file_size;

    struct stat mystat;
    if (stat(path, &mystat) < 0) {
        logerror("%s: stat file %s failed.\n", __func__, path);
        return content;
    }
    file_size = mystat.st_size;

    if (size > 0 && file_size > size) {
        logerror("%s: %s file too large(%d > %d).\n", __func__, path,
                  file_size, size);
        return content;
    }

    if ((content = malloc(file_size + 1)) == NULL) {
        logerror("%s: allocate memory failed.\n", __func__);
        return content;
    }

    int fp;
    if ((fp = open(path, O_RDONLY)) < 1) {
        logerror("%s: open %s failed.\n", __func__, path);
        free(content);
        content = NULL;
        return content;
    }

    int bytes;
    int bytes_total = 0;
    int to_read = file_size;
    char *p = content;
    while ((bytes = read(fp, p, to_read)) > 0) {
        bytes_total += bytes;
        p += bytes;
        if (to_read > (file_size - bytes_total)) {
            to_read = file_size - bytes_total;
        }
    }
    close(fp);

    if (bytes < 0) {
        logerror("%s: read from %s failed.\n", __func__, path);
        free(content);
        content = NULL;
        return content;
    }

    *p = '\0';
    return content;
}

/* 
** execute system(shell_command) and return stdout in new string
** pointed to by *stringp 
*/
char *system_output(char *shell_command)
{
    char *buf = NULL;
    FILE *fp;

    /* forks off command (this doesn't fail if command doesn't exist */
    logdebug(_("system_output(): [%s]\n"), shell_command);
    if ((fp = popen(shell_command, "r")) == NULL)
        return NULL;            /* caller can check errno */
    buf = fp2str(fp, 0);

    pclose(fp);
    return buf;
}

/* run a system command */
int system_call(char *cmd)
{
    logdebug(_("System call \"%s\".\n"), cmd);

    if (system(cmd)) {
        return -1;
    }

    return 0;
}

/* "touch" a file, creating if necessary */
int touch(const char *path)
{
    int ret = 0;
    int fd;

    if ((fd = open(path, O_WRONLY | O_CREAT | O_NONBLOCK, 0644)) >= 0) {
        close(fd);
        if (utime(path, NULL) != 0) {
            logerror(_("error: touch(): failed to adjust time for %s (%s)\n"),
                       path, strerror(errno));
            ret = 1;
        }
    }
    else {
        /* suppress error message 
        logerror(_("error: touch(): failed to create/open file %s (%s)\n"),
                   path, strerror(errno));
        */
        ret = 1;
    }
    return ret;
}

/* diffs two files: 0=same, -N=different, N=error */
int diff(const char *path1, const char *path2)
{
    int fd1, fd2;
    char buf1[BUFSIZE], buf2[BUFSIZE];

    if ((fd1 = open(path1, O_RDONLY)) < 0) {
        logerror(_("error: diff(): failed to open %s\n"), path1);
        return -1;
    }
    else if ((fd2 = open(path2, O_RDONLY)) < 0) {
        logerror(_("error: diff(): failed to open %s\n"), path2);
        close(fd1);
        return -1;
    }
    else {
        int read1, read2;
        do {
            read1 = read(fd1, buf1, BUFSIZE);
            read2 = read(fd2, buf2, BUFSIZE);
            if (read1 != read2)
                break;
            if (read1 && memcmp(buf1, buf2, read1))
                break;
        } while (read1);
        close(fd1);
        close(fd2);
        return (-(read1 + read2));      /* both should be 0s if files are equal */
    }
    return -1;
}

/*
** print out runtime info, see following manpages 
**  sysconf(3) pathconf(3) 
*/
void print_os_runtime_info(void)
{
    printf("\nCurrent os enviroment:\n\n");

    printf("%48s", "_SC_LINE_MAX : ");
#ifdef _SC_LINE_MAX
    printf("%ld\n", sysconf(_SC_LINE_MAX));
#else
    printf("not support.\n");
#endif

    printf("%48s", "_SC_CLK_TCK : ");
#ifdef _SC_CLK_TCK
    printf("%ld\n", sysconf(_SC_CLK_TCK));
#else
    printf("not support.\n");
#endif

    printf("%48s", "_SC_THREAD_DESTRUCT_OR_ITERATIONS : ");
#ifdef _SC_THREAD_DESTRUCT_OR_ITERATIONS
    printf("%ld\n", sysconf(_SC_THREAD_DESTRUCT_OR_ITERATIONS));
#else
    printf("not support.\n");
#endif

    printf("%48s", "_SC_THREAD_STACK_MIN : ");
#ifdef _SC_THREAD_STACK_MIN
    printf("%ld\n", sysconf(_SC_THREAD_STACK_MIN));
#else
    printf("not support.\n");
#endif

    printf("%48s", "_SC_THREAD_THREADS_MAX : ");
#ifdef _SC_THREAD_THREADS_MAX
    printf("%ld\n", sysconf(_SC_THREAD_THREADS_MAX));
#else
    printf("not support.\n");
#endif

    printf("%48s", "_PC_PATH_MAX : ");
#ifdef _PC_PATH_MAX
    printf("%ld\n", pathconf("/etc/hosts", _PC_PATH_MAX));
#else
    printf("not support.\n");
#endif

    printf("%48s", "_PC_NAME_MAX : ");
#ifdef _PC_NAME_MAX
    printf("%ld\n", pathconf("/etc/hosts", _PC_NAME_MAX));
#else
    printf("not support.\n");
#endif

    printf("\n\n");
}

