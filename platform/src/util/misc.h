#ifndef __LY_INCLUDE_UTIL_MISC_H
#define __LY_INCLUDE_UTIL_MISC_H

typedef unsigned char boolean;
#define TRUE 1
#define FALSE 0

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
    logprintfl(LYDEBUG, "OP TIME (%s): %f\n", #a, b - a);     \
  }


int str_filter_white_space(char *str);
int file_not_exist(char *file);
char *file2str(const char *path, int size);       /* read file 'path' into a new string */
char *fp2str(FILE * fp, int size);
int touch(const char *path);
int diff(const char *path1, const char *path2);

char *system_output(char *shell_command);
int system_call(char *cmd);
int system_loop_mount(const char *src, const char *dest, const char *options);
int system_loop_umount(const char *src, const char *dest);

/* print the useful information of current system. */
void print_os_runtime_info(void);

#endif
