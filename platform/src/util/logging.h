#ifndef __LY_INCLUDE_UTIL_LOGGING_H
#define __LY_INCLUDE_UTIL_LOGGING_H

/* Something about i18n */
#include <locale.h>
#include <libintl.h>
#ifndef _
#define _(S) gettext(S)
#endif
#define LOCALEDIR "/usr/share/locale"

/* The max size of log file */
#define MAXLOGFILESIZE 32768000

/* the max of log message sent to logging callback */
#define LOG_CALLBACK_MSG_MAX 100

enum { LYDEBUG, LYINFO, LYWARN, LYERROR, LYFATAL };

/* dan's functions */
int logfile(const char *file, int in_loglevel);
int logsimple(const char *format, ...);
int logprintf(const char *format, ...);
int logprintfl(int level, const char *format, ...);

/* static int lylogprintfl(int level, const char *format, va_list ap); */
int logdebug(const char *format, ...);
int logerror(const char *format, ...);
int loginfo(const char *format, ...);
int logwarn(const char *format, ...);
int logclose(void);

/* allow caller to specify callback function for log messages */
int logcallback(void (* func)(), int data);

#endif 
