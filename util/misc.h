/* Some function that may be useful

   ref: util/misc.h of Eucalyptus */


#ifndef __LUOYU_UTIL_misc_INCLUDE_H
#define __LUOYU_UTIL_misc_INCLUDE_H


#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h> /* strlen, strcpy */
#include <ctype.h> /* isspace */
#include <stdarg.h>
#include <sys/types.h>
#define _FILE_OFFSET_BITS 64
#include <sys/stat.h>
#include <unistd.h>
#include <time.h>
#include <fcntl.h> /* open */
#include <utime.h> /* utime */
#include <sys/wait.h>
#include <sys/types.h>
#include <dirent.h> /* opendir, etc */
#include <errno.h> /* errno */
#include <sys/time.h> /* gettimeofday */
#include <limits.h>

#include "luoyun.h"


typedef unsigned char boolean;
#define TRUE 1
#define FALSE 0

#ifndef MAX_PATH
#define MAX_PATH 4096
#endif

#define TIMERSTART(a) double a;                                 \
  {                                                             \
    struct timeval UBERSTART;                                   \
    gettimeofday(&UBERSTART, NULL);                             \
    a = UBERSTART.tv_sec + (UBERSTART.tv_usec / 1000000.0);     \
  }

#define TIMERSTOP(a) {                                          \
    struct timeval UBERSTOP;                                    \
    double b;                                                   \
    gettimeofday(&UBERSTOP, NULL);                              \
    b = UBERSTOP.tv_sec + (UBERSTOP.tv_usec / 1000000.0);       \
    logprintfl(EUCADEBUG, "OP TIME (%s): %f\n", #a, b - a);     \
  }


enum {LYDEBUG, LYINFO, LYWARN, LYERROR, LYFATAL};


char * fp2str(FILE * fp);
char * system_output(char * shell_command );

/* dan's functions */
int logfile(const char *file, int in_loglevel);
int logsimple(const char *format, ...);
int logprintf(const char *format, ...);
int logprintfl(int level, const char *format, ...);

int lylogprintfl(int level, const char *format, va_list ap);
int logdebug(const char *format, ...);
int logerror(const char *format, ...);
int loginfo(const char *format, ...);
int logwarn(const char *format, ...);

int check_directory(char *dir);
int check_file(char *file);

int touch (const char * path);
int diff (const char * path1, const char * path2);
char * file2str (const char * path); /* read file 'path' into a new string */


#endif
