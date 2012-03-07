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
#include <string.h>
#include <ctype.h>
#include <stdarg.h>
#include <pthread.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>             
#include <limits.h>

#include "osmlog.h"

#ifndef MAX_PATH
#define MAX_PATH PATH_MAX
#endif

static int logging = 0; 
static int loglevel = LYWARN;
static FILE *LOGFH = NULL;
static char logFile[MAX_PATH];
static pthread_mutex_t log_mutex = PTHREAD_MUTEX_INITIALIZER;

/*
** initialize logging related syste variables
*/
int logfile(const char *file, int in_loglevel)
{
    if (in_loglevel >= LYDEBUG && in_loglevel <= LYINFO)
        printf("logging started\n");

    /* pthread_mutex_init(&log_mutex, NULL); */

    logging = 0;
    if (in_loglevel >= LYDEBUG && in_loglevel <= LYFATAL) {
        loglevel = in_loglevel;
    }
    else {
        loglevel = LYDEBUG;
    }
    if (file == NULL) {
        LOGFH = NULL;
    }
    else {
        if (LOGFH != NULL) {
            fclose(LOGFH);
        }

        snprintf(logFile, MAX_PATH, "%s", file);
        LOGFH = fopen(file, "a");
        if (LOGFH) {
            logging = 1;
        }
    }
    return (1 - logging);
}

/*
** simply logging without priority check and message tagging
*/
int logsimple(const char *format, ...)
{
    pthread_mutex_lock(&log_mutex);
    va_list ap;
    int rc;
    FILE *file;

    rc = 1;
    va_start(ap, format);

    if (logging) {
        file = LOGFH;
    }
    else {
        file = stdout;
    }
    rc = vfprintf(file, format, ap);
    fflush(file);

    va_end(ap);
    pthread_mutex_unlock(&log_mutex);
    return (rc);
}

/*
** simply logging with message tag(current time), but without priority check
*/
int logprintf(const char *format, ...)
{
    pthread_mutex_lock(&log_mutex);
    va_list ap;
    int rc;
    char buf[27], *eol;
    time_t t;
    FILE *file;

    rc = 1;
    va_start(ap, format);

    if (logging) {
        file = LOGFH;
    }
    else {
        file = stdout;
    }

    t = time(NULL);
    if (ctime_r(&t, buf)) {
        eol = strchr(buf, '\n');
        if (eol) {
            *eol = '\0';
        }
        fprintf(file, "[%s] ", buf);
    }
    rc = vfprintf(file, format, ap);
    fflush(file);

    va_end(ap);
    pthread_mutex_unlock(&log_mutex);
    return (rc);
}

static int lylogprintfl(int level, const char *format, va_list ap)
{
    int rc, fd;
    char buf[27], *eol;
    time_t t;
    struct stat statbuf;
    FILE *file;

    if (level < loglevel) {
        return (0);
    }

    pthread_mutex_lock(&log_mutex);

    rc = 1;

    if (logging) {
        file = LOGFH;
        fd = fileno(file);
        if (fd >= 0) {
            rc = fstat(fd, &statbuf);
            if (!rc && ((int) statbuf.st_size > MAXLOGFILESIZE)) {
                int i;
                char oldFile[MAX_PATH], newFile[MAX_PATH];

                rc = stat(logFile, &statbuf);
                if (!rc && ((int) statbuf.st_size > MAXLOGFILESIZE)) {
                    for (i = 4; i >= 0; i--) {
                        snprintf(oldFile, MAX_PATH, "%s.%d", logFile, i);
                        snprintf(newFile, MAX_PATH, "%s.%d", logFile,
                                 i + 1);
                        rename(oldFile, newFile);
                    }
                    snprintf(oldFile, MAX_PATH, "%s", logFile);
                    snprintf(newFile, MAX_PATH, "%s.%d", logFile, 0);
                    rename(oldFile, newFile);
                }
                fclose(LOGFH);
                LOGFH = fopen(logFile, "a");
                if (LOGFH) {
                    file = LOGFH;
                }
                else {
                    file = stdout;
                }
            }
        }
    }
    else {
        file = stdout;
    }

    t = time(NULL);
    if (ctime_r(&t, buf)) {
        eol = strchr(buf, '\n');
        if (eol) {
            *eol = '\0';
        }
        fprintf(file, "[%s]", buf);
    }

    /**
     * DD -- DEBUG
     * II -- INFO
     * WW -- WARN
     * EE -- ERROR
     * FF -- FATAL
     */
    /* fprintf(file, "[%06d]", getpid()); */
    if (level == LYDEBUG) {
        fprintf(file, "[DD] ");
    }
    else if (level == LYINFO) {
        fprintf(file, "[II] ");
    }
    else if (level == LYWARN) {
        fprintf(file, "[WW] ");
    }
    else if (level == LYERROR) {
        fprintf(file, "[EE] ");
    }
    else if (level == LYFATAL) {
        fprintf(file, "[FF] ");
    }
    else {
        fprintf(file, "[DD] ");
    }
    rc = vfprintf(file, format, ap);
    fflush(file);

    pthread_mutex_unlock(&log_mutex);
    return (rc);
}

int logerror(const char *format, ...)
{
    int rc;
    va_list ap;
    va_start(ap, format);
    rc = lylogprintfl(LYERROR, format, ap);
    va_end(ap);

    return (rc);
}

int logdebug(const char *format, ...)
{
    int rc;
    va_list ap;
    va_start(ap, format);
    rc = lylogprintfl(LYDEBUG, format, ap);
    va_end(ap);
    return (rc);
}

int loginfo(const char *format, ...)
{
    int rc;
    va_list ap;
    va_start(ap, format);
    rc = lylogprintfl(LYINFO, format, ap);
    va_end(ap);
    return (rc);
}

int logwarn(const char *format, ...)
{
    int rc;
    va_list ap;
    va_start(ap, format);
    rc = lylogprintfl(LYWARN, format, ap);
    va_end(ap);

    return (rc);
}

/* close log file */
int logclose(void)
{
    if (LOGFH != NULL){
       fclose(LOGFH);
       LOGFH = NULL;
    }
    return 0;
}
