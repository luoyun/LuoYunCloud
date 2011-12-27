/* Define the global things woulb be needed by LuoYun. */

#ifndef __LUOYUN_INCLUDE_LUOYUN_H
#define __LUOYUN_INCLUDE_LUOYUN_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdint.h>

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

#define LY_PATH_MAX 512
#define LY_LINE_MAX 1024
#define LY_NAME_MAX 256


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



/* New request format */

typedef enum RequestTarget_t {
     RQTARGET_WEB = 1,
     RQTARGET_CONTROL = 2,
     RQTARGET_COMPUTE = 3,
     RQTARGET_VOS = 4,
     RQTARGET_INSTANCE = 4,
} RequestTarget;

typedef enum RequestType_t {
     RQTYPE_REGISTER = 1,
     RQTYPE_KEEP_ALIVE = 2,
     RQTYPE_NEW_JOB = 10,
     RQTYPE_DOMAIN_CONTROL = 20,
     RQTYPE_INSTANCE_REGISTER = 30,
} RequestType;

typedef int RequestLength;
typedef int DataLength;

typedef struct LyRequest_t {
     RequestTarget from;
     RequestType type;
     RequestLength length;
} LyRequest;


typedef enum RespondStatus_t {
     RESPOND_STATUS_OK = 0,
     RESPOND_STATUS_FAILED = 1,
} RespondStatus;

typedef struct LyRespond_t {
     RespondStatus status;
     DataLength    length;
} LyRespond;


#pragma pack(1)
typedef struct DomainControlData_t {
     int32_t id;
     int8_t  action;
} DomainControlData;
#pragma pack()

/* Node struct needed by control server and compute server. */

typedef enum NodeStatus_t {
     NODE_S_UNKNOWN = 0,
     NODE_S_STOP = 1,
     NODE_S_RUNNING = 2,
     NODE_S_NEED_QUERY = 10,
     NODE_S_QUERYING = 11,
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
#pragma pack(1)
typedef struct ComputeNodeInfo_t {
     int64_t max_memory;
     int64_t free_memory;
     int16_t max_cpus;
     int16_t cpu_mhz;
     int16_t load_average;
     int16_t port;
     int8_t  active_flag;
     int8_t  status;
     int8_t  arch;             /* cpu arch */
     int8_t  hypervisor;
     int8_t  network_type;
     char    cpu_model[32];
     char    hostname[32];
     char    ip[32];          /* eg 192.168.0.1 */
} ComputeNodeInfo;
#pragma pack()


typedef enum DomainStatus_t {
     DOMAIN_S_UNKNOWN = 0,
     DOMAIN_S_STOP = 1,
     DOMAIN_S_RUNNING = 2,
     DOMAIN_S_SUSPEND = 3,
     DOMAIN_S_MIGERATE = 4,
} DomainStatus;

#if 0
typedef struct DomainInfo_t {
     DomainStatus status;
     int id;                 /* id in DB */
     char name[32];
     char uuid[64];
     int node;               /* node id in DB */
     int image_id;           /* image id */
     int diskimg;            /* old: diskimg id in DB */
     int kernel;             /* old: kernel image id in DB */
     int initrd;             /* old: initrd image id in DB */
     char boot[64];          /* old: bood order */
     unsigned cpus;          /* numbers of cpu */
     unsigned long memory;   /* size of memory */

     char ip[32];            /* domain's first ip */
     char mac[32];           /* mac of first NIC */

     time_t created;
     time_t updated; /* old */
} DomainInfo;

#endif

#pragma pack(1)
typedef struct DomainInfo_t {
     int64_t memory;         /* size of memory */
     int32_t id;             /* id in DB */
     int32_t node_id;        /* node id in DB */
     int32_t image_id;       /* image id */
     int8_t  cpus;           /* numbers of cpu */
     int8_t  status;
     char    ip[32];         /* domain's first ip */
} DomainInfo;
#pragma pack()


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

#pragma pack(1)
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
#pragma pack()

/* some useful function */
int create_socket(const char *node, const char *service);
int create_and_bind(char *port);
int make_socket_non_blocking(int sfd);
/* print the useful information of current system. */
void lyu_os_runtime_info(void);
void lyu_daemonize(const char *log, int loglevel);

int connect_to_host (char *host, int port);
int lyu_make_sure_dir_exist (const char *dir);
int lyu_decompress_bzip2 ( const char *srcfile,
                           const char *dstfile );
int lyu_decompress_gz ( const char *srcfile,
                        const char *dstfile );
int str_filter_white_space( char *str );


int lyu_system_call(char *cmd);


#define RECV_TIMEOUT 60
#define SEND_TIMEOUT 60

int ly_recv(int sfd, void *buf, size_t length, int flags, int timeout);
int ly_send(int sfd, const void *buf, size_t length, int flags, int timeout);

#endif

