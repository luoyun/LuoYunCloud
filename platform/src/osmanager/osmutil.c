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
#include <strings.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <memory.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <limits.h>
#include <uuid/uuid.h>
#include <signal.h>

#include "osmutil.h"

#ifndef MAX_PATH
#define MAX_PATH PATH_MAX
#endif

/*
** create socket from given host(ip string)/port and connect to it
*/
int lyutil_connect_to_host(char *host, int port)
{
    if (host == NULL)
        return -1;

    int sk;
    sk = socket(AF_INET, SOCK_STREAM, 0);
    if (sk == -1)
        return -1;

    struct sockaddr_in servaddr;
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(port);
    servaddr.sin_addr.s_addr = inet_addr(host);
    bzero(&(servaddr.sin_zero), 8);

    int err;
    err = connect(sk, (struct sockaddr *) &servaddr, sizeof(servaddr));
    if (0 != err) {
        close(sk);
        return -1;
    }

    return sk;
}

/* change socket to nonblocking mode */
int lyutil_make_socket_nonblocking(int sfd)
{
    int flags, s;

    flags = fcntl(sfd, F_GETFL, 0);
    if (flags == -1)
        return -1;

    flags |= O_NONBLOCK;
    s = fcntl(sfd, F_SETFL, flags);
    if (s == -1)
        return -1;

    return 0;
}

/* get local ip of connected socket */
/*
** note:
** struct sockaddr {
**     sa_family_t sa_family;
**     char        sa_data[14];
** }
**
** struct sockaddr_in {
**     sa_family_t           sin_family;
**     unsigned short int    sin_port; 
**     struct in_addr        sin_addr;
**     //Pad to size of `struct sockaddr'.
**     unsigned char         __pad[__SOCK_SIZE__ - sizeof(short int) -
**                           sizeof(unsigned short int) - sizeof(struct in_addr)];
** };
**
** struct in_addr {
**     __u32   s_addr;
** };
**
*/
char * lyutil_get_local_ip(int sd)
{
    struct sockaddr addr;
    int len = sizeof(addr);;
    if (getsockname(sd, &addr, (unsigned *)&len) != 0)
        return NULL;

    if (addr.sa_family != AF_INET)
        return NULL;

    char * ip = inet_ntoa(((struct sockaddr_in *)(&addr))->sin_addr);
    if (ip == NULL)
        return NULL;

    return strdup(ip);
}

/* set up keepalive for the socket */
int lyutil_set_keepalive(int sd, int time, int intvl, int probes)
{
    int start = 1;
    if (setsockopt(sd, SOL_SOCKET, SO_KEEPALIVE, &start, sizeof(int)) < 0)
        return -1;
    if (setsockopt(sd, SOL_TCP, TCP_KEEPIDLE, &time, sizeof(int)) < 0)
        return -1;
    if (setsockopt(sd, SOL_TCP, TCP_KEEPINTVL, &intvl, sizeof(int)) < 0)
        return -1;
    if (setsockopt(sd, SOL_TCP, TCP_KEEPCNT, &probes, sizeof(int)) < 0)
        return -1;
    return 0;
}

/* ref APUE2 */
/*
** daemonize the process with tty detached, files closed, pwd changed to root
*/
void lyutil_daemonize()
{
    pid_t pid;
    struct rlimit rl;
    struct sigaction sa;

    /* Clear file creation mask. */
    umask(0);

    /* Get Maximum number of file descriptiors. */
    if (getrlimit(RLIMIT_NOFILE, &rl) < 0) {
        perror("can't get file limit");
        exit(1);
    }

    /* Become a session leader to lose controlling TTY. */
    if ((pid = fork()) < 0) {
        perror("can not fork");
        exit(2);
    }
    else if (pid != 0)
        exit(0);
    setsid();

    /* ensure future opens won't allocate controlling TTYs. */
    sa.sa_handler = SIG_IGN;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    if (sigaction(SIGHUP, &sa, NULL) < 0) {
        perror("can not ignore SIGHUP");
        exit(3);
    }
    if ((pid = fork()) < 0) {
        perror("can not fork");
        exit(4);
    }
    else if (pid != 0)
        exit(0);

    /* Change the current working directory to the root
       so we won't prevent file systems from being unmounted. */
    if (chdir("/") < 0) {
        perror("can not change directory to /");
        exit(5);
    }

    /* Close all open file descriptors. */
    if (rl.rlim_max == RLIM_INFINITY)
        rl.rlim_max = 1024;
    int i;
    for (i = 0; i < rl.rlim_max; i++)
        close(i);

    /* Attach file descriptors 0, 1, and 2 to /dev/null. */
#if 0
    int fd0, fd1, fd2;
    fd0 = open("/dev/null", O_RDWR);
    fd1 = dup(0);
    fd2 = dup(0);
#endif
}

/* 
** improved util func based on lyutil_create_dir
*/
int lyutil_create_file(const char *path, int dir_only)
{
    char * tmp;
    int i, len;

    if (path == NULL)
        return -1;

    len = strlen(path);
    if (len == 0 || (path[len-1] == '/' && dir_only == 0))
        return -1;

    tmp = strdup(path);
    if (tmp == NULL)
        return -1;

    /* dir */
    for (i = 1; i < len; i++) {
        if (tmp[i] == '/') {
            tmp[i] = '\0';
            if (access(tmp, R_OK) != 0 &&
                mkdir(tmp, 0755) == -1) {
                free(tmp);
                return -1;
            }
            tmp[i] = '/';
        }
    }

    /* file */
    if (tmp[i-1] != '/' && dir_only == 0 && access(tmp, F_OK) != 0) {
        int fd = creat(tmp, 0644);
        if (fd < 0) {
            free(tmp);
            return -1;
        }
        close(fd);
    }

    free(tmp);
    return 0;
}

/* generate uuid string */
char * lyutil_uuid(char * in, int in_len)
{
    if (in && in_len < LUOYUN_UUID_STR_LEN)
        return NULL;
    if (in == NULL) {
        in = malloc(LUOYUN_UUID_STR_LEN);
        if (in == NULL)
            return NULL;
        bzero(in, LUOYUN_UUID_STR_LEN);
    }
    uuid_t u;
    uuid_generate(u);
    uuid_unparse(u, in);
    return in;
}
