/* Define the global things woulb be needed by LuoYun. */

#ifndef __LUOYUN_INCLUDE_LUOYUN_H
#define __LUOYUN_INCLUDE_LUOYUN_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

/* The max size of log file, needed by misc.c */
#define MAXLOGFILESIZE 32768000


/* Something about i18n */
#include <locale.h>
#include <libintl.h>
#define _(S) gettext(S)
#define LOCALEDIR "/usr/share/locale"


/* The max length of a line buffer. */
#ifndef LINE_MAX
#define LINE_MAX 1024
#endif

#define MAX_IP_LEN 64
#define MAX_MAC_LEN 64
#define MAX_USERNAME_LEN 64
#define MAX_PASSWORD_LEN 64
#define MAX_PATH_LEN 256



typedef struct LySockHead_t {
     int type;
     int length;
} LySockHead;


typedef enum LySockTarget_t {
     LST_WEB_S = 1,
     LST_CONTROL_S = 2,
     LST_COMPUTE_S = 3,
     LST_VOS_S = 4,
} LySockTarget;

typedef enum LyAction_t {
     LA_UNKNOWN = 0,

     // web action
     LA_WEB_NEW_JOB = 11,

     // ComPute node action
     LA_CP_UPDATE_STATUS = 21,
     LA_DOMAIN_STATUS = 22,

     // ConTrol node action
     LA_CT_GET_NODE_STATUS = 41,
     LA_CONTROL_DOMAIN = 42,

     // TODO: should mixture with JobAction in 
     //       control/job_manager.h
     LA_DOMAIN_RUN = 51,
     LA_DOMAIN_STOP = 52,
     LA_DOMAIN_SUSPEND = 53,
     LA_DOMAIN_SAVE = 54,
     LA_DOMAIN_REBOOT = 55,

     LA_CP_GET_IMAGE_INFO = 61,
} LyAction;


/* Request and Respond must be used in one connect socket. */

typedef struct LySockRequest_t {
     LySockTarget from;         /* from where */
     LySockTarget to;           /* to who */
     int type;         /* GET or PUST, like http */
     LyAction action;  /* like url, LuoYun specifiled */
     int datalen;      /* Data length */
} LySockRequest;

typedef struct LySockRequestHandler_t {
     LySockRequest *request;
     int sk;
} LySockRequestHandler;


typedef struct LySockRespond_t {
     LySockTarget from;
     LySockTarget to;
     int status;       /* the status of action exec */
     int used_time;    /* used time of the action exec */
     int datalen;
} LySockRespond;


/* Node struct needed by control server and compute server. */

typedef enum NodeStatus_t {
     NODE_S_UNKNOWN = 0,
     NODE_S_STOP = 1,
     NODE_S_RUNNING = 2,
} NodeStatus;

typedef enum HypervisorType_t {
     HYPERVISOR_IS_UNKNOWN = 0,
     HYPERVISOR_IS_KVM = 1,
     HYPERVISOR_IS_XEN = 2,
} HypervisorType;

typedef enum CpuArch_t {
     CPU_ARCH_UNKNOWN = 0,
     CPU_ARCH_X86 = 1,
     CPU_ARCH_X86_64 = 2,
} CpuArch;

#include <time.h>
typedef struct ComputeNodeInfo_t {
     NodeStatus status;

     char hostname[30];
     char ip[32];          /* eg 192.168.0.1 */
     int port;
     CpuArch arch;             /* cpu arch */
     HypervisorType hypervisor;
     unsigned long hypervisor_version;
     unsigned long libversion;
     int network_type;

     unsigned long long max_memory;
     int max_cpus;
     char cpu_model[32];
     int cpu_mhz;

     int load_average;
     unsigned long long free_memory;

     time_t created;
     time_t updated;

     int active_flag;

} ComputeNodeInfo;


typedef enum DomainStatus_t {
     DOMAIN_S_UNKNOWN = 0,
     DOMAIN_S_STOP = 1,
     DOMAIN_S_RUNNING = 2,
     DOMAIN_S_SUSPEND = 3,
     DOMAIN_S_MIGERATE = 4,
} DomainStatus;

typedef struct DomainInfo_t {
     DomainStatus status;
     int id;                 /* id in DB */
     char name[32];
     char uuid[64];
     int node;               /* node id in DB */
     int diskimg;            /* diskimg id in DB */
     int kernel;             /* kernel image id in DB */
     int initrd;             /* initrd image id in DB */
     char boot[64];          /* bood order */
     unsigned cpus;          /* numbers of cpu */
     unsigned long memory;   /* size of memory */

     char ip[32];            /* domain's first ip */
     char mac[32];           /* mac of first NIC */

     time_t created;
     time_t updated;
} DomainInfo;


typedef enum ImageType_t {
     IMAGE_IS_KERNEL = 1,
     IMAGE_IS_RAMDISK = 2,
     IMAGE_IS_DISK = 3,
     IMAGE_IS_ISO = 4,
} ImageType;

typedef enum ChecksumType_t {
     CHECKSUM_BY_MD5 = 1,
     CHECKSUM_BY_SHA1 = 2,
} ChecksumType;

typedef struct ImageInfo_t {
     int id;
     char name[32];
     ImageType type;
     ChecksumType checksum_type;
     char checksum_value[128];
     unsigned long size;
     time_t created;
     time_t updated;
} ImageInfo;


/* some useful function */
int create_socket(const char *node, const char *service);
/* print the useful information of current system. */
void lyu_os_runtime_info(void);
void lyu_daemonize(const char *log);

int connect_to_host (char *host, int port);
int lyu_make_sure_dir_exist (const char *dir);
int lyu_decompress_bzip2 ( const char *srcfile,
                           const char *dstfile );
int lyu_decompress_gz ( const char *srcfile,
                        const char *dstfile );
int str_filter_white_space( char *str );
#endif

