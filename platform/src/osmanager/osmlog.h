#ifndef __LY_INCLUDE_OSMANAGER_OSMLOG_H
#define __LY_INCLUDE_OSMANAGER_OSMLOG_H

/* The max size of log file */
#define MAXLOGFILESIZE 32768000

enum { LYDEBUG, LYINFO, LYWARN, LYERROR, LYFATAL };

int logfile(const char *file, int in_loglevel);
int logsimple(const char *format, ...);
int logdebug(const char *format, ...);
int logerror(const char *format, ...);
int loginfo(const char *format, ...);
int logwarn(const char *format, ...);
int logclose(void);

#endif 
