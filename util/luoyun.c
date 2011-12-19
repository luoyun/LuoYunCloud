#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <limits.h>
#include <unistd.h>
#include <sys/resource.h>
#include <signal.h>

#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h> /* gethostname */
#include <netdb.h> /* struct hostent */

#include <time.h>

#include "luoyun.h"
#include "misc.h"


void lyu_os_runtime_info(void)
{
     printf("\nCurrent os enviroment:\n\n");

     printf("%48s", "_SC_LINE_MAX : ");
#ifdef _SC_LINE_MAX
     printf("%ld\n", sysconf(_SC_LINE_MAX));
#else
     printf("not support.\n");
#endif

     printf("%48s", "_SC_CLK_TCK : ");
#ifdef _SC_CLK_TCK
     printf("%ld\n", sysconf(_SC_CLK_TCK));
#else
     printf("not support.\n");
#endif

     printf("%48s", "_SC_THREAD_DESTRUCT_OR_ITERATIONS : ");
#ifdef _SC_THREAD_DESTRUCT_OR_ITERATIONS
     printf("%ld\n", sysconf(_SC_THREAD_DESTRUCT_OR_ITERATIONS));
#else
     printf("not support.\n");
#endif

     printf("%48s", "_SC_THREAD_STACK_MIN : ");
#ifdef _SC_THREAD_STACK_MIN
     printf("%ld\n", sysconf(_SC_THREAD_STACK_MIN));
#else
     printf("not support.\n");
#endif

     printf("%48s", "_SC_THREAD_THREADS_MAX : ");
#ifdef _SC_THREAD_THREADS_MAX
     printf("%ld\n", sysconf(_SC_THREAD_THREADS_MAX));
#else
     printf("not support.\n");
#endif

     printf("%48s", "_PC_PATH_MAX : ");
#ifdef _PC_PATH_MAX
     printf("%ld\n", pathconf("/etc/hosts", _PC_PATH_MAX));
#else
     printf("not support.\n");
#endif

     printf("%48s", "_PC_NAME_MAX : ");
#ifdef _PC_NAME_MAX
     printf("%ld\n", pathconf("/etc/hosts", _PC_NAME_MAX));
#else
     printf("not support.\n");
#endif

     printf("\n\n");
}


/* ref APUE2 */
void lyu_daemonize(const char *log)
{
     pid_t pid;
     struct rlimit rl;
     struct sigaction sa;

     /* Clear file creation mask. */
     umask(0);

     /* Get Maximum number of file descriptiors. */
     if (getrlimit(RLIMIT_NOFILE, &rl) < 0)
     {
          perror("can't get file limit");
          exit(1);
     }

     /* Become a session leader to lose controlling TTY. */
     if ((pid = fork()) < 0)
     {
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
     if (sigaction(SIGHUP, &sa, NULL) < 0)
     {
          perror("can not ignore SIGHUP");
          exit(3);
     }
     if ((pid = fork()) < 0)
     {
          perror("can not fork");
          exit(4);
     }
     else if (pid != 0)
          exit(0);

     /* Change the current working directory to the root
        so we won't prevent file systems from being unmounted. */
     if (chdir("/") < 0)
     {
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
     /* Initialize the log file */
     logfile(log, LYDEBUG);
}



/* create a socket and listen on it 

   returns: socket if OK, -1 on error. */
int create_socket(const char *node, const char *service)
{
     int sfd;
     int err;

     struct addrinfo hints, *result=NULL, *rp=NULL;

     memset(&hints, 0, sizeof(hints));
     hints.ai_family = AF_INET;
     hints.ai_socktype = SOCK_STREAM;
     hints.ai_flags = AI_ALL;
     hints.ai_protocol = 0;
     hints.ai_canonname = NULL;
     hints.ai_addr = NULL;
     hints.ai_next = NULL;

     err = getaddrinfo(node, service, &hints, &result);

     if ( 0 != err )
     {
          fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(err));
          return -1;
     }


     for(rp = result; rp != NULL; rp = rp->ai_next)
     {

          sfd = socket(rp->ai_family, rp->ai_socktype,
                       rp->ai_protocol);
          if ( -1 == sfd )
               continue;

          if ( 0 == bind(sfd, rp->ai_addr, rp->ai_addrlen) &&
               0 == listen(sfd, 5) )
          {
               char ip[INET_ADDRSTRLEN];
               struct sockaddr_in *sinp = (struct sockaddr_in *) rp->ai_addr;
               inet_ntop(rp->ai_family, &sinp->sin_addr, ip, INET_ADDRSTRLEN);
               printf("Listen on: %s:%d\n", ip, ntohs(sinp->sin_port));
               break;
          }
#if 0
          char ip[INET_ADDRSTRLEN];
          struct sockaddr_in *sinp;
          close(sfd);
          sinp = (struct sockaddr_in *) rp->ai_addr;
          memset(ip, 0, INET_ADDRSTRLEN);
          switch(rp->ai_family)
          {
          case AF_INET:
          case AF_INET6:
               inet_ntop(rp->ai_family, &sinp->sin_addr, ip, INET_ADDRSTRLEN);
               printf("ip = %s, port = %d\n", ip, ntohs(sinp->sin_port));
          }
#endif

     }

     if ( NULL == rp )
     {
          fprintf(stderr, "Could not bind.\n");
          return -1;
     }


     freeaddrinfo(result);

     return sfd;
}


int
connect_to_host (char *host, int port)
{
     int sk; /* socket fd */
     sk = socket(AF_INET, SOCK_STREAM, 0);

     struct sockaddr_in servaddr;
     servaddr.sin_family = AF_INET;
     servaddr.sin_port = htons(port);
     servaddr.sin_addr.s_addr = inet_addr(host);
     bzero(&(servaddr.sin_zero), 8);

     int err;
     err = connect(sk, (struct sockaddr *)&servaddr, sizeof(servaddr));
     if ( 0 != err )
     {
          logprintfl(LYERROR, "connect to %s:%d error.\n", host, port);
          return -1;
     }

     return sk;
}


int lyu_make_sure_dir_exist (const char *dir)
{
  
     char *tmpdir;
     int i, len;
     tmpdir = malloc (strlen (dir) + 1);

     strcpy (tmpdir, dir);
     if (tmpdir[strlen (tmpdir) - 1] != '/')
          strcat (tmpdir, "/");

     len = strlen (tmpdir);
     for (i=1; i<len; i++) {
          if (tmpdir[i] == '/') {
               tmpdir[i] = '\0';
               if (access (tmpdir, R_OK) != 0) {
                    if (mkdir (tmpdir, 0755) == -1) {
                         logprintfl(LYERROR, "Couldn't create the directory: %s\n", tmpdir);
                         return 1;
                    }
               }
               tmpdir[i] = '/';
          }
     }

     free (tmpdir);
     return 0;
}


#include <bzlib.h>
/* decompress the file with zlib */
int
lyu_decompress_bzip2 ( const char *srcfile,
                       const char *dstfile )
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

#define BZ_BUF_SIZE 10240
     FILE*   f;
     BZFILE* b;
     int     nBuf;
     char    buf[BZ_BUF_SIZE];
     int     bzerror;
     //int     nWritten;

     f = fopen ( srcfile, "r" );
     if ( !f ) {
          /* handle error */
          logprintfl(LYERROR, "%s: Open %s error.\n",
                     __func__, srcfile);
     }
     b = BZ2_bzReadOpen ( &bzerror, f, 0, 0, NULL, 0 );
     if ( bzerror != BZ_OK ) {
          BZ2_bzReadClose ( &bzerror, b );
          /* handle error */
     }

     FILE*   t;
     t = fopen( dstfile, "w" );
     if ( !t )
     {
          logprintfl(LYERROR, "Open %s error.\n", dstfile);
     }

     bzerror = BZ_OK;
     //logsimple("Begin ...\n");
     while ( bzerror == BZ_OK) {
          //logsimple(".");
          nBuf = BZ2_bzRead ( &bzerror, b, buf, BZ_BUF_SIZE );
          if ( bzerror == BZ_OK ) {
               /* do something with buf[0 .. nBuf-1] */
          }
          fwrite(buf, nBuf, 1, t);
     }
     //logsimple("\nEnd ...\n");
     if ( bzerror != BZ_STREAM_END ) {
          BZ2_bzReadClose ( &bzerror, b );
          /* handle error */
     } else {
          BZ2_bzReadClose ( &bzerror, b );
     }

     fclose(t);
     return 0;
}


#include <zlib.h>
/* decompress the file with zlib */
int
lyu_decompress_gz ( const char *srcfile,
                    const char *dstfile )
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

#define GZ_BUF_SIZE 10240

     gzFile in = gzopen(srcfile, "rb");
     FILE *out = fopen(dstfile, "wb");
     if (!in || !out) return -1;

     char buffer[GZ_BUF_SIZE];
     int num_read = 0;
     while ((num_read = gzread( in, buffer,
                                sizeof(buffer))) > 0)
     {
          fwrite(buffer, 1, num_read, out);
     }

     gzclose(in);
     fclose(out);

     return 0;
}


/* filter the white space in str. eg ' ', '\t', comment . */
int str_filter_white_space( char *str )
{
     int i, j;
     int length = strlen( str );
     char newstr[LINE_MAX] = {'\0'};

     for ( i = 0, j = 0; i < length; i++)
          if ( str[i] != ' ' &&
               str[i] != '\t' &&
               str[i] != '\n' )
               newstr[j++] = str[i];

     if ( (*newstr == '#') || (*newstr == ';') )
          *newstr = '\0';

     newstr[j] = '\0';
     strcpy( str, newstr );

     return 0;
}



int
lyu_system_call(char *cmd)
{
     int ret;

     ret = system(cmd);

     if (ret == -1)
     {
          logprintfl(LYERROR, "system call error: %s", cmd);
          return -3;
     } else if (ret != 0) {
          logprintfl(LYERROR, "cmd error: %s", cmd);
          return -4;
     }

     return 0;
}
