#include "misc.h"
#include <pthread.h>


#define BUFSIZE 1024

int logging=0; /* The switch */
int loglevel=LYDEBUG;
FILE *LOGFH=NULL;
char logFile[MAX_PATH];
pthread_mutex_t log_mutex = PTHREAD_MUTEX_INITIALIZER;


int file_exist(char *file) {
  int rc;
  struct stat mystat;
  
  if (!file) {
    return(1);
  }
  
  rc = lstat(file, &mystat);
  if (rc < 0 || !S_ISREG(mystat.st_mode)) {
    return(1);
  }
  return(0);
}


char * fp2str (FILE * fp)
{
#   define INCREMENT 512
  int buf_max = INCREMENT;
  int buf_current = 0;
  char * last_read;
  char * buf = NULL;

  if (fp==NULL) return NULL;
  do {
    // create/enlarge the buffer
    void * new_buf;
    if ((new_buf = realloc (buf, buf_max)) == NULL) {
      if ( buf != NULL ) { // previous realloc()s worked
	free (buf); // free partial buffer
      }
      return NULL;
    }
    buf = new_buf;
    logprintfl (LYDEBUG, "fp2str: enlarged buf to %d\n", buf_max);

    do { // read in until EOF or buffer is full
      last_read = fgets (buf+buf_current, buf_max-buf_current, fp);
      if ( last_read != NULL )
	buf_current = strlen(buf);
      logprintfl (LYDEBUG, "fp2str: read %d characters so far (max=%d, last=%s)\n", buf_current, buf_max, last_read?"no":"yes");
    } while ( last_read && buf_max > buf_current+1 ); /* +1 is needed for fgets() to put \0 */
        
    buf_max += INCREMENT; /* in case it is full */
  } while (last_read);

  if ( buf_current < 1 ) {
    free (buf);
    buf = NULL;
  }

  return buf;
}


/* execute system(shell_command) and return stdout in new string
 * pointed to by *stringp */
char * system_output (char * shell_command )
{
  char * buf = NULL;
  FILE * fp;

  /* forks off command (this doesn't fail if command doesn't exist */
  logprintfl (LYDEBUG, "system_output(): [%s]\n", shell_command);
  if ( (fp=popen(shell_command, "r")) == NULL) 
    return NULL; /* caller can check errno */
  buf = fp2str (fp);

  pclose(fp);
  return buf;
}


int logfile(const char *file, int in_loglevel) {
  printf("START %s:%d:%s\n", __FILE__, __LINE__, __func__);
  //pthread_mutex_init(&log_mutex, NULL);

  logging = 0;
  if (in_loglevel >= LYDEBUG && in_loglevel <= LYFATAL) {
    loglevel = in_loglevel;
  } else {
    loglevel = LYDEBUG;
  }
  if (file == NULL) {
    LOGFH = NULL;
  } else {
    if (LOGFH != NULL) {
      fclose(LOGFH);
    }
    
    snprintf(logFile, MAX_PATH, "%s", file);
    LOGFH = fopen(file, "a");
    if (LOGFH) {
      logging=1;
    }
  }
  return(1-logging);
}


int logsimple(const char *format, ...) {
  pthread_mutex_lock(&log_mutex);
  va_list ap;
  int rc;
  FILE *file;
  
  rc = 1;
  va_start(ap, format);
  
  if (logging) {
    file = LOGFH;
  } else {
    file = stdout;
  }
  rc = vfprintf(file, format, ap);
  fflush(file);
  
  va_end(ap);
  pthread_mutex_unlock(&log_mutex);
  return(rc);
}


int logprintf(const char *format, ...) {
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
  } else {
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
  return(rc);
}

int logprintfl(int level, const char *format, ...) {
  va_list ap;
  int rc, fd;
  char buf[27], *eol;
  time_t t;
  struct stat statbuf;
  FILE *file;
  
  if (level < loglevel) {
    return(0);
  }

  pthread_mutex_lock(&log_mutex);
  
  rc = 1;
  va_start(ap, format);
  
  if (logging) {
    file = LOGFH;
    fd = fileno(file);
    if (fd > 0) {
      rc = fstat(fd, &statbuf);
      if (!rc && ((int)statbuf.st_size > MAXLOGFILESIZE)) {
	int i;
	char oldFile[MAX_PATH], newFile[MAX_PATH];
	
	rc = stat(logFile, &statbuf);
	if (!rc && ((int)statbuf.st_size > MAXLOGFILESIZE)) {
	  for (i=4; i>=0; i--) {
	    snprintf(oldFile, MAX_PATH, "%s.%d", logFile, i);
	    snprintf(newFile, MAX_PATH, "%s.%d", logFile, i+1);
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
	} else {
	  file = stdout;
	}
      }
    }
  } else {
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
  if (level == LYDEBUG) {fprintf(file, "[DD] ");}
  else if (level == LYINFO) {fprintf(file, "[II] ");}
  else if (level == LYWARN) {fprintf(file, "[WW] ");}
  else if (level == LYERROR) {fprintf(file, "[EE] ");}
  else if (level == LYFATAL) {fprintf(file, "[FF] ");}
  else {fprintf(file, "[DD] ");}
  rc = vfprintf(file, format, ap);
  fflush(file);
  
  va_end(ap);
  pthread_mutex_unlock(&log_mutex);
  return(rc);
}

int lylogprintfl(int level, const char *format, va_list ap) {
  int rc, fd;
  char buf[27], *eol;
  time_t t;
  struct stat statbuf;
  FILE *file;
  
  if (level < loglevel) {
    return(0);
  }

  pthread_mutex_lock(&log_mutex);
  
  rc = 1;
  
  if (logging) {
    file = LOGFH;
    fd = fileno(file);
    if (fd > 0) {
      rc = fstat(fd, &statbuf);
      if (!rc && ((int)statbuf.st_size > MAXLOGFILESIZE)) {
	int i;
	char oldFile[MAX_PATH], newFile[MAX_PATH];
	
	rc = stat(logFile, &statbuf);
	if (!rc && ((int)statbuf.st_size > MAXLOGFILESIZE)) {
	  for (i=4; i>=0; i--) {
	    snprintf(oldFile, MAX_PATH, "%s.%d", logFile, i);
	    snprintf(newFile, MAX_PATH, "%s.%d", logFile, i+1);
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
	} else {
	  file = stdout;
	}
      }
    }
  } else {
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
  if (level == LYDEBUG) {fprintf(file, "[DD] ");}
  else if (level == LYINFO) {fprintf(file, "[II] ");}
  else if (level == LYWARN) {fprintf(file, "[WW] ");}
  else if (level == LYERROR) {fprintf(file, "[EE] ");}
  else if (level == LYFATAL) {fprintf(file, "[FF] ");}
  else {fprintf(file, "[DD] ");}
  rc = vfprintf(file, format, ap);
  fflush(file);
  
  pthread_mutex_unlock(&log_mutex);
  return(rc);
}

int logerror(const char *format, ...)
{
     int rc;
     va_list ap;
     va_start(ap, format);
     rc = lylogprintfl(LYERROR, format, ap);
     va_end(ap);
     return(rc);
}

int logdebug(const char *format, ...)
{
     int rc;
     va_list ap;
     va_start(ap, format);
     rc = lylogprintfl(LYDEBUG, format, ap);
     va_end(ap);
     return(rc);
}

int loginfo(const char *format, ...)
{
     int rc;
     va_list ap;
     va_start(ap, format);
     rc = lylogprintfl(LYINFO, format, ap);
     va_end(ap);
     return(rc);
}

int logwarn(const char *format, ...)
{
     int rc;
     va_list ap;
     va_start(ap, format);
     rc = lylogprintfl(LYWARN, format, ap);
     va_end(ap);
     return(rc);
}


/* "touch" a file, creating if necessary */
int touch (const char * path)
{
    int ret = 0;
    int fd;
    
    if ( (fd = open (path, O_WRONLY | O_CREAT | O_NONBLOCK, 0644)) >= 0 ) {
        close (fd);
        if (utime (path, NULL)!=0) {
            logprintfl (LYERROR, "error: touch(): failed to adjust time for %s (%s)\n", path, strerror (errno));
            ret = 1;
        }
    } else {
        logprintfl (LYERROR, "error: touch(): failed to create/open file %s (%s)\n", path, strerror (errno));
        ret = 1;
    }
    return ret;
}

/* diffs two files: 0=same, -N=different, N=error */
int diff (const char * path1, const char * path2)
{
    int fd1, fd2;
    char buf1 [BUFSIZE], buf2 [BUFSIZE];

    if ( (fd1 = open (path1, O_RDONLY)) < 0 ) {
        logprintfl (LYERROR, "error: diff(): failed to open %s\n", path1);
    } else if ( (fd2 = open (path2, O_RDONLY)) < 0 ) {
        logprintfl (LYERROR, "error: diff(): failed to open %s\n", path2);
    } else {
        int read1, read2;
        do {
            read1 = read (fd1, buf1, BUFSIZE);
            read2 = read (fd2, buf2, BUFSIZE);
            if (read1!=read2) break;
            if (read1 && memcmp (buf1, buf2, read1)) break;
        } while (read1);
        close (fd1);
        close (fd2);
        return (-(read1 + read2)); /* both should be 0s if files are equal */
    }
    return -1;
}


/* read file 'path' into a new string */
char * file2str (const char * path)
{
     char * content = NULL;
     int file_size;

     struct stat mystat;
     if (stat (path, &mystat) < 0){
          logerror("%s: stat file %s failed.\n", __func__, path);
          return content;
     }
     file_size = mystat.st_size;

     if ( (content = malloc (file_size+1)) == NULL ) {
          logerror("%s: allocate memory failed.\n", __func__);
          return content;
     }

     int fp;
     if ( ( fp = open (path, O_RDONLY) ) < 1 )
     {
          logerror("%s: open %s failed.\n", __func__, path);
          free (content);
          content = NULL;
          return content;
     }

     int bytes;
     int bytes_total = 0;
     int to_read = (SSIZE_MAX)<file_size?(SSIZE_MAX):file_size;
     char * p = content;
     while ( (bytes = read (fp, p, to_read)) > 0) {
          bytes_total += bytes;
          p += bytes;
          if (to_read > (file_size-bytes_total)) {
               to_read = file_size-bytes_total;
          }
     }
     close(fp);

     if ( bytes < 0 ) {
          logerror("%s: read from %s failed.\n", __func__, path);
          free (content);
          content = NULL;
          return content;
     }

     * p = '\0';
     return content;
}
