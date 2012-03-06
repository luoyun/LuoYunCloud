#ifndef __LY_INCLUDE_OSMANAGER_OSMMISC_H
#define __LY_INCLUDE_OSMANAGER_OSMMISC_H

int str_filter_white_space(char *str);
int touch(const char *path);
char *system_output(char *shell_command);
int system_call(char *cmd);

#endif
