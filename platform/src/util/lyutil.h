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
#ifndef __LY_INCLUDE_UTIL_LYUTIL_H
#define __LY_INCLUDE_UTIL_LYUTIL_H

/* socket helpers */
int lyutil_create_socket(const char *node, const char *service);
int lyutil_create_and_bind(char *port);
int lyutil_make_socket_nonblocking(int sfd);
int lyutil_connect_to_host(char *host, int port);
char * lyutil_get_local_ip(int sd);
int lyutil_set_keepalive(int sd, int time, int intvl, int probes);

/* daemonize the program */
void lyutil_daemonize(void (* exit_func)(), int exit_data);

/* directory manipulation */
int lyutil_create_dir(const char *dir);
int lyutil_create_file(const char *path, int dir_only);

/* process lock file */
int lyutil_check_pid_file(const char *path, const char *name);
int lyutil_create_pid_file(const char *path, const char *name);
int lyutil_remove_pid_file(const char *path, const char *name);

/* file decompression */
int lyutil_decompress_bzip2(const char *srcfile, const char *dstfile);
int lyutil_decompress_gz(const char *srcfile, const char *dstfile);

/* file checksum checking */
int lyutil_checksum(char *filename, char *checksum);

/* generate uuid string */
#define LUOYUN_UUID_STR_LEN 40
char *lyutil_uuid(char * in, int in_len);

/* system info */
#define LOAD_AVERAGE_LAST_1M  1
#define LOAD_AVERAGE_LAST_5M  2
#define LOAD_AVERAGE_LAST_15M 3
int lyutil_load_average(int type);
unsigned long long lyutil_free_memory(void);

int lyutil_signal_init();

#endif
