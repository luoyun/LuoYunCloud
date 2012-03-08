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
#ifndef __LY_INCLUDE_OSMANAGER_OSMUTIL_H
#define __LY_INCLUDE_OSMANAGER_OSMUTIL_H

/* socket helpers */
int lyutil_make_socket_nonblocking(int sfd);
int lyutil_connect_to_host(char *host, int port);
char * lyutil_get_local_ip(int sd);
int lyutil_set_keepalive(int sd, int time, int intvl, int probes);

/* daemonize the program */
void lyutil_daemonize(void);

/* directory manipulation */
int lyutil_create_file(const char *path, int dir_only);

/* generate uuid string */
#define LUOYUN_UUID_STR_LEN 40
char *lyutil_uuid(char * in, int in_len);

#endif
