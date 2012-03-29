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
#include <bzlib.h>
#include <zlib.h>

#include "logging.h"
#include "md5.h" /* curtosy of www.fourmilab.ch */
#include "lyutil.h"

#ifndef MAX_PATH
#define MAX_PATH PATH_MAX
#endif

/* 
** create a IPv4/TCP socket and listen on it 
**
** returns: socket if OK, -1 on error. 
*/
int lyutil_create_socket(const char *node, const char *service)
{
    int sfd = -1;

    struct addrinfo hints, *result = NULL, *rp = NULL;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_ALL;
    hints.ai_protocol = 0;
    hints.ai_canonname = NULL;
    hints.ai_addr = NULL;
    hints.ai_next = NULL;

    int err = getaddrinfo(node, service, &hints, &result);
    if (err != 0) {
        logerror(_("error getaddrinfo: %s\n"), gai_strerror(err));
        return -1;
    }

    for (rp = result; rp != NULL; rp = rp->ai_next) {

        sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (-1 == sfd)
            continue;

        if (0 == bind(sfd, rp->ai_addr, rp->ai_addrlen) &&
            0 == listen(sfd, 5)) {
            char ip[INET_ADDRSTRLEN];
            struct sockaddr_in *sinp = (struct sockaddr_in *) rp->ai_addr;
            inet_ntop(rp->ai_family, &sinp->sin_addr, ip, INET_ADDRSTRLEN);
            loginfo(_("Listen on: %s:%d\n"), ip, ntohs(sinp->sin_port));
            break;
        }
        else
            close(sfd);

#if 0
        char ip[INET_ADDRSTRLEN];
        struct sockaddr_in *sinp;
        close(sfd);
        sinp = (struct sockaddr_in *) rp->ai_addr;
        memset(ip, 0, INET_ADDRSTRLEN);
        switch (rp->ai_family) {
        case AF_INET:
        case AF_INET6:
            inet_ntop(rp->ai_family, &sinp->sin_addr, ip, INET_ADDRSTRLEN);
            printf("ip = %s, port = %d\n", ip, ntohs(sinp->sin_port));
        }
#endif

    }

    if (result)
        freeaddrinfo(result);

    if (NULL == rp) {
        logerror(_("%s(%s, %s) failed.\n"), __func__, node, service);
        return -1;
    }

    return sfd;
}

/*
** create a TCP socket and bind on it 
*/
int lyutil_create_and_bind(char *port)
{
    struct addrinfo hints;
    struct addrinfo *result, *rp;
    int sfd;

    memset(&hints, 0, sizeof(struct addrinfo));
#if 0
    hints.ai_family = AF_UNSPEC;        /* Return IPv4 and IPv6 choices */
#else
    hints.ai_family = AF_INET;  /* IPv4 only */
#endif
    hints.ai_socktype = SOCK_STREAM;    /* We want a TCP socket */
    hints.ai_flags = AI_PASSIVE;        /* All interfaces */

    int err = getaddrinfo(NULL, port, &hints, &result);
    if (err != 0) {
        logerror(_("error getaddrinfo: %s\n"), gai_strerror(err));
        return -1;
    }

    for (rp = result; rp != NULL; rp = rp->ai_next) {
        sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (sfd == -1)
            continue;

        /* Fix me: Enable address reuse, for DEBUG */
        int on = 1;
        setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on));
        if (sfd == -1)
            continue;

        err = bind(sfd, rp->ai_addr, rp->ai_addrlen);
        if (err == 0) {
            /* We managed to bind successfully! */
            break;
        }

        close(sfd);
    }

    if (result)
        freeaddrinfo(result);

    if (rp == NULL) {
        logerror(_("%s(%s) failed.\n"), __func__, port);
        return -1;
    }

    return sfd;
}

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
        logerror(_("connect to %s:%d error(%d).\n"), host, port, errno);
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
    if (flags == -1) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }

    flags |= O_NONBLOCK;
    s = fcntl(sfd, F_SETFL, flags);
    if (s == -1) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }

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

    /*
    char hbuf[NI_MAXHOST], sbuf[NI_MAXSERV];
    int ret = getnameinfo(&addr, len, hbuf, sizeof(hbuf),
                          sbuf, sizeof(sbuf),
                          NI_NUMERICHOST | NI_NUMERICSERV);
    if (ret)
        return NULL;
    return strdup(hbuf);
    */
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

/*
** daemonize the process with tty detached, files closed, pwd changed to root
*/
void lyutil_daemonize(void (* exit_func)(), int exit_data)
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
    else if (pid != 0) {
        if (exit_func)
            exit_func(exit_data);
        exit(0);
    }
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
    else if (pid != 0) {
        if (exit_func)
            exit_func(exit_data);
        exit(0);
    }

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
** util func to create direcotry if doesn't exist
** when needed, it creates all the parent directories.
*/
int lyutil_create_dir(const char *dir)
{
    char *tmpdir;
    int i, len;

    tmpdir = malloc(strlen(dir) + 2);
    if (tmpdir == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }

    strcpy(tmpdir, dir);
    if (tmpdir[strlen(tmpdir) - 1] != '/')
        strcat(tmpdir, "/");

    len = strlen(tmpdir);
    for (i = 1; i < len; i++) {
        if (tmpdir[i] == '/') {
            tmpdir[i] = '\0';
            if (access(tmpdir, R_OK) != 0) {
                if (mkdir(tmpdir, 0755) == -1) {
                    logerror("mkdir %s failed in %s\n", tmpdir, __func__);
                    return -1;
                }
            }
            tmpdir[i] = '/';
        }
    }

    free(tmpdir);
    return 0;
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


/* 
** check lock file with pid of running process 
** return 0: not exist, 1: exist already, -1: error
*/
int lyutil_check_pid_file(const char *dir, const char *name)
{
    if (dir == NULL || name == NULL)
        return -1;

    /* check whether it's writable */
    if (access(dir, W_OK)) {
        logerror(_("directory %s not writable\n"), dir);
        return -1;
    }

    char path[MAX_PATH];
    if (snprintf(path, MAX_PATH, "%s/%s.pid", dir, name) >= MAX_PATH) {
        logerror(_("path max exceeded %s\n"), __func__);
        return -1;
    }

    /* check proc fs should be mounted */
    /* assume it's mounted on /proc, but it may not be true... */
    char tmpstr[20];
    bzero(tmpstr, 20);
    if (readlink("/proc/self", tmpstr, 10) <= 0 ||
        (pid_t) atoi(tmpstr) != getpid()) {
        logerror(_
                 ("reading /proc error, please make sure it's mounted\n"));
        return -1;
    }

    /* check whether programs is started already */
    FILE *fp = fopen(path, "r");
    if (fp != NULL) {
        int pid;
        if (fscanf(fp, "%d", &pid) != 1) {
            fclose(fp);
            return 0;
        }
        fclose(fp);

        /* check whether the process is this program */
        sprintf(tmpstr, "/proc/%d/stat", pid);
        fp = fopen(tmpstr, "r");
        if (fp == NULL) {
            loginfo(_
                    ("process pid file is found, but process doesn't exist. "
                     "old pid file ignored.\n"));
            return 0;
        }
        if (fscanf(fp, "%*s (%20s", tmpstr) != 1) {
            logerror(_("reading /proc error %s\n"), __func__);
            return -1;
        }
        fclose(fp);

        int namelen = strlen(name);
        if (strlen(tmpstr) == namelen + 1 &&
            strncmp(tmpstr, name, namelen) == 0) {
            loginfo(_("program started already.\n"));
            return 1;
        }
        loginfo(_
                ("process pid file is found, but program doesn't seem running."
                 "old pid file ignored.\n"));
    }

    return 0;
}

/* 
** create lock file with pid of running process 
** return 0: sucess, 1: exist already, -1: error
*/
int lyutil_create_pid_file(const char *dir, const char *name)
{
    int ret = lyutil_check_pid_file(dir, name);
    if (ret != 0)
        return ret;

    char path[MAX_PATH];
    if (snprintf(path, MAX_PATH, "%s/%s.pid", dir, name) >= MAX_PATH) {
        logerror(_("path max exceeded %s\n"), __func__);
        return -1;
    }

#if 0
    FILE *fp = fopen(path, "w");
    if (fp == NULL) {
        logerror(_("Failed writing to %s\n"), path);
        return -1;
    }
    fprintf(fp, "%d", getpid());
    fclose(fp);
#else
    int fd = creat(path, S_IWUSR|S_IRUSR);
    if (fd < 0) {
        logerror(_("Failed creating %s\n"), path);
        return -1;
    }
    char pid[10];
    snprintf(pid, 10, "%d", getpid());
    write(fd, pid, strlen(pid));
    close(fd);
#endif

    return 0;
}

/* remove pid file */
int lyutil_remove_pid_file(const char *dir, const char *name)
{
    if (dir == NULL || name == NULL)
        return -1;

    char path[MAX_PATH];
    if (snprintf(path, MAX_PATH, "%s/%s.pid", dir, name) >= MAX_PATH) {
        logerror(_("path max exceeded %s\n"), __func__);
        return -1;
    }
    unlink(path);

    return 0;
}

/* decompress the file with zlib */
int lyutil_decompress_bzip2(const char *srcfile, const char *dstfile)
{
#define BZ_BUF_SIZE 10240
    int nBuf;
    char buf[BZ_BUF_SIZE];
    BZFILE * b = NULL;
    int bzerror;
    FILE *f = NULL, *t = NULL;
    int ret = -1;

    f = fopen(srcfile, "r");
    if (!f) {
        logerror("open %s failed.\n", srcfile);
        return -1;
    }
    t = fopen(dstfile, "w");
    if (!t) {
        logerror("open %s failed.\n", dstfile);
        goto out;
    }

    b = BZ2_bzReadOpen(&bzerror, f, 0, 0, NULL, 0);
    if (bzerror != BZ_OK) {
        logerror("BZ2_bzReadOpen %s failed.\n", srcfile);
        goto out;
    }

    bzerror = BZ_OK;
    while (bzerror == BZ_OK) {
        nBuf = BZ2_bzRead(&bzerror, b, buf, BZ_BUF_SIZE);
        if (fwrite(buf, nBuf, 1, t) != nBuf) {
            logerror(_("writing %s failed.\n"), dstfile);
            goto out;
        }
    }
    if (bzerror != BZ_STREAM_END) {
        logerror(_("BZ2_bzRead %s error.\n"), srcfile);
        goto out;
    }

    ret = 0;
out:
    if (b)
        BZ2_bzReadClose(&bzerror, b);
    if (f)
        fclose(f);
    if (t)
        fclose(t);
    return ret;
}

/* decompress the file with zlib */
int lyutil_decompress_gz(const char *srcfile, const char *dstfile)
{
    gzFile in = gzopen(srcfile, "rb");
    if (!in) {
        logerror(_("open %s failed.\n"), srcfile);
        return -1;
    }
    FILE *out = fopen(dstfile, "wb");
    if (!in) {
        logerror(_("open %s failed.\n"), dstfile);
        gzclose(in);
        return -1;
    }
    int ret = -1;

#define GZ_BUF_SIZE 10240
    char buffer[GZ_BUF_SIZE];
    int num_read = 0;
    while ((num_read = gzread(in, buffer, sizeof(buffer))) > 0) {
        if (fwrite(buffer, 1, num_read, out) != num_read) {
            logerror(_("writing %s failed.\n"), dstfile);
            goto out;
        }
    }

    ret = 0;
out:
    gzclose(in);
    fclose(out);
    return ret;
}


/* file checksum checking */
int lyutil_checksum(char *filename, char *checksum)
{
    unsigned char buffer[16384], signature[16];
    struct MD5Context md5c;

    if (filename == NULL || checksum == NULL)
        return -1;

    if (strlen(checksum) != 32) {
        logerror("checksum(%s) is %d long, probably not md5?\n", checksum, 32);
        return -1;
    }

    FILE * in = fopen(filename, "rb");
    if (in == NULL) {
        logerror("open %s failed.\n", filename);
        return -1;
    }

    int j;
    MD5Init(&md5c);
    while ((j = (int) fread(buffer, 1, sizeof buffer, in)) > 0) {
        MD5Update(&md5c, buffer, (unsigned) j);
    }

    fclose(in);
    MD5Final(signature, &md5c);

    char t[3];
    t[2] = 0;
    for (j=0; j<16; j++) {
        t[0] = checksum[j<<1];
        t[1] = checksum[(j<<1)+1];
        if (signature[j] != (unsigned char)strtol(t, NULL, 16))
            return 1;
    }
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

/* system info, system load average */
int lyutil_load_average(int type)
{
    float f = 0.0;
    FILE *fp = NULL;
    fp = fopen("/proc/loadavg", "r");
    if (fp == NULL) {
        logerror(_("can not open file %s\n"), "/proc/loadavg");
        return -1;
    }
    if (type == LOAD_AVERAGE_LAST_1M)
        fscanf(fp, "%f", &f);
    else if (type == LOAD_AVERAGE_LAST_5M)
        fscanf(fp, "%*f %f", &f);
    else
        /* type == LOAD_AVERAGE_LAST_15M */
        fscanf(fp, "%*f %*f %f", &f);
    fclose(fp);
    return f*100;
}

/* system info, system memory available to use */
unsigned long long lyutil_free_memory(void)
{
    long i, free = -1, buffers = -1, cached = -1;
    char s[41];
    FILE *fp = NULL;
    fp = fopen("/proc/meminfo", "r");
    if (fp == NULL) {
        logerror(_("can not open file %s\n"), "/proc/meminfo");
        return 0;
    }
    while (fscanf(fp, "%40s %ld kB\n", s, &i) != EOF) {
        if (strncmp("MemFree:", s, 40) == 0)
            free = i;
        else if (strncmp("Buffers:", s, 40) == 0)
            buffers = i;
        else if (strncmp("Cached:", s, 40) == 0)
            cached = i;
        if (free != -1 && buffers != -1 && cached != -1)
            break;
    }
    fclose(fp);

    if (free == -1 || buffers == -1 || cached == -1) {
        logerror(_("Failed finding required fields in /proc/meminfo\n"));
        return 0;
    }

    return (free + buffers + cached);
}

/* logging signal before calling default/old handler */
static void __signal_handler_default(int signo)
{
    logwarn(_("received signal: %d, %s\n"), signo, strsignal(signo));
    signal(signo, SIG_DFL);
    raise(signo);
    return;
}

/* init default behavior of handling signals */
int lyutil_signal_init()
{
    int signo;
    for (signo = 1; signo < NSIG; signo++)
        signal(signo, __signal_handler_default);

    return 0;
}
