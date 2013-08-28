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

/* Define the global things woulb be needed by LuoYun. */

#ifndef __LY_INCLUDE_LUOYUN_H
#define __LY_INCLUDE_LUOYUN_H

#include <sys/types.h>

#define MAX_IP_LEN 64
#define MAX_MAC_LEN 64
#define MAX_USERNAME_LEN 64
#define MAX_PASSWORD_LEN 64

/* entities in system */
typedef enum EntityType_t {
    LY_ENTITY_UNKNOWN  = 0,
    LY_ENTITY_WEB      = 1,
    LY_ENTITY_CLC      = 2,
    LY_ENTITY_NODE     = 3,
    LY_ENTITY_OSM      = 4,
} EntityType;
#define JOB_TARGET_INSTANCE LY_ENTITY_OSM
#define JOB_TARGET_NODE LY_ENTITY_NODE

/*
** Constants of actions initiated from all entities
**
** Each entity taks a sub-set of the following actions.
*/
typedef enum LYAction_t {
     LY_A_UNKNOWN = 0,

     /* 
     ** actions taken by clc
     */
     LY_A_CLC_SCAN_NODE = 101,
     LY_A_CLC_ENABLE_NODE = 102,
     LY_A_CLC_DISABLE_NODE = 103,
     LY_A_CLC_CONFIG_NODE = 104,
     LY_A_CLC_REGISTER_NODE = 111,

     /* 
     ** actions taken by node to control instances
     */
     LY_A_NODE_RUN_INSTANCE = 201,
     LY_A_NODE_STOP_INSTANCE = 202,
     LY_A_NODE_SUSPEND_INSTANCE = 203,
     LY_A_NODE_SAVE_INSTANCE = 204,
     LY_A_NODE_FULLREBOOT_INSTANCE = 205,
     LY_A_NODE_DESTROY_INSTANCE = 206,
     LY_A_NODE_QUERY_INSTANCE = 207,
     LY_A_NODE_ACPIREBOOT_INSTANCE = 208,

     /*
     ** actions taken by node to control node
     */
     LY_A_NODE_QUERY = 251,

     /*
     ** actions taken by OS manager to control instance itself
     */
     LY_A_OSM_QUERY = 301,
} LYAction;

typedef enum LYActionStatus_t {
     LY_S_UNKNOWN = 0,
     LY_S_INITIATED = 100,
     LY_S_RUNNING = 200,
     LY_S_RUNNING_SEARCHING_NODE = 201,
     LY_S_RUNNING_SENT_TO_NODE = 202,
     LY_S_RUNNING_WAITING = 210,
     LY_S_RUNNING_DOWNLOADING_APP = 211,
     LY_S_RUNNING_CHECKING_APP = 212,
     LY_S_RUNNING_EXTRACTING_APP = 213,
     LY_S_RUNNING_MOUNTING_IMAGE = 214,
     LY_S_RUNNING_PREPARING_IMAGE = 215,
     LY_S_RUNNING_UNMOUNTING_IMAGE = 216,
     LY_S_RUNNING_STARTING_INSTANCE = 221,
     LY_S_RUNNING_STOPPING = 250,
     LY_S_RUNNING_STOPPED = 259,
     LY_S_RUNNING_LAST_STATUS = 299,
     LY_S_FINISHED = 300,
     LY_S_FINISHED_SUCCESS = 301,
     LY_S_FINISHED_INSTANCE_RUNNING = 302,
     LY_S_FINISHED_INSTANCE_NOT_RUNNING = 303,
     LY_S_FINISHED_INSTANCE_NOT_EXIST = 304,
     LY_S_FINISHED_FAILURE = 311,
     LY_S_FINISHED_FAILURE_NODE_NOT_AVAIL = 321,
     LY_S_FINISHED_FAILURE_NODE_BUSY = 322,
     LY_S_FINISHED_FAILURE_NODE_NOT_ENABLED = 323,
     LY_S_FINISHED_FAILURE_NODE_NOT_ONLINE = 324,
     LY_S_FINISHED_FAILURE_NODE_NOT_REGISTERED = 325,
     LY_S_FINISHED_FAILURE_APP_DOWNLOAD = 331,
     LY_S_FINISHED_FAILURE_APP_ERROR = 332,
     LY_S_FINISHED_LAST_STATUS = 399,
     LY_S_WAITING = 400,
     LY_S_WAITING_STARTING_OSM = 411,
     LY_S_WAITING_SYCING_OSM = 412,
     LY_S_WAITING_STARTING_SERVICE = 421,
     LY_S_WAITING_LAST_STATUS = 499,
     LY_S_PENDING = 500,
     LY_S_PENDING_NODE_STROKE = 501,
     LY_S_PENDING_LAST_STATUS = 599,
     LY_S_TIMEOUT = 600,
     LY_S_CANCEL = 700,
     LY_S_CANCEL_INTERNAL_ERROR = 701,
     LY_S_CANCEL_ALREADY_EXIST = 702,
     LY_S_CANCEL_TARGET_BUSY = 703,
     LY_S_CANCEL_ACTION_REPLACED = 711,
     LY_S_CANCEL_LAST_STATUS = 799,
     LY_S_REGISTERING_INIT = 1001,
     LY_S_REGISTERING_CONFIG = 1005,
     LY_S_REGISTERING_REINIT = 1011,
     LY_S_REGISTERING_DONE_SUCCESS = 1021,
     LY_S_REGISTERING_DONE_FAIL = 1022,
     /* 2000 - 2127 matches (2000 + <exit value of app status program>) */
     LY_S_APP_RUNNING = 2000,
     LY_S_APP_UNKNOWN = 2128,
     LY_S_APP_STOPPED = 2129,
     LY_S_APP_FAILED = 2130
} LYActionStatus;
#define JOB_IS_INITIATED(s) (s == LY_S_INITIATED)
#define JOB_IS_STARTED(s) (s == LY_S_RUNNING)
#define JOB_IS_RUNNING(s) (s >= LY_S_RUNNING && s < LY_S_RUNNING_LAST_STATUS)
#define JOB_IS_FINISHED(s) (s >= LY_S_FINISHED && s < LY_S_FINISHED_LAST_STATUS)
#define JOB_IS_WAITING(s) (s >= LY_S_WAITING && s < LY_S_WAITING_LAST_STATUS)
#define JOB_IS_TIMEOUT(s) (s == LY_S_TIMEOUT)
#define JOB_IS_PENDING(s) (s >= LY_S_PENDING && s < LY_S_PENDING_LAST_STATUS)
#define JOB_IS_CANCELLED(s) (s >= LY_S_CANCEL && s < LY_S_CANCEL_LAST_STATUS)
#define JOB_S_UNKNOWN LY_S_UNKNOWN
#define JOB_S_INITIATED LY_S_INITIATED 
#define JOB_S_RUNNING LY_S_RUNNING
#define JOB_S_FINISHED LY_S_FINISHED_SUCCESS
#define JOB_S_FAILED LY_S_FINISHED_FAILURE
#define JOB_S_TIMEOUT LY_S_TIMEOUT
#define JOB_S_PENDING LY_S_PENDING

/*
** Each packet transmitted between entities must have a header
** Interpretion of packet that follows the packet header depends on the 
** packet type specified in packet header.
*/
#pragma pack(1)
typedef struct LYPacketHeader_t {
    int32_t type;
    int32_t length;
} LYPacketHeader;
#pragma pack()

/*
** Constants for LYPacketHeader type field 
** 
** The value for each member of PacketType must be carefully chosen,
** as the memebers are grouped depending on the value.
**
** All requests are represented by positive odd numbers, and the even numbers
** that are immediately followed are conresponding replies. If no reply
** is exprected for a request, the corresponding even number will be
** skipped.
**
** All the requests are further grouped based on requests' origins.
**   10001 - 19997, are requests originated from LY_ENTITY_WEB
**   20001 - 29997, are requests originated from LY_ENTITY_CLC
**   30001 - 39997, are requests originated from LY_ENTITY_NODE
**   40001 - 49997, are requests originated from LY_ENTITY_WEB
**
*/
#define PKT_TYPE_ENTITY_GROUP_SIZE 10000
typedef enum PacketType_t {
    PKT_TYPE_UNKNOW = 0,
    PKT_TYPE_JOIN_REQUEST = 101,
    PKT_TYPE_TEST_ECHO_REQUEST = 901,
    PKT_TYPE_TEST_ECHO_REPLY = 902,
    PKT_TYPE_WEB = 10000,
    PKT_TYPE_WEB_NEW_JOB_REQUEST = 10001,
    PKT_TYPE_WEB_NEW_JOB_REPLY = 10002,
    PKT_TYPE_CLC = 20000,
    PKT_TYPE_CLC_INSTANCE_CONTROL_REQUEST = 20011,
    PKT_TYPE_CLC_INSTANCE_CONTROL_REPLY = 20012,
    PKT_TYPE_CLC_NODE_CONTROL_REQUEST = 20021,
    PKT_TYPE_CLC_NODE_CONTROL_REPLY = 20022,
    PKT_TYPE_CLC_OSM_QUERY_REQUEST = 20033,
    PKT_TYPE_CLC_OSM_QUERY_REPLY = 20034,
    PKT_TYPE_NODE = 30000,
    PKT_TYPE_NODE_REGISTER_REQUEST = 30001,
    PKT_TYPE_NODE_REGISTER_REPLY = 30002,
    PKT_TYPE_NODE_REPORT = 30003,
    PKT_TYPE_NODE_AUTH_REQUEST = 30011,
    PKT_TYPE_NODE_AUTH_REPLY = 30012,
    PKT_TYPE_OSM = 40000,
    PKT_TYPE_OSM_REGISTER_REQUEST = 40001,
    PKT_TYPE_OSM_REGISTER_REPLY = 40002,
    PKT_TYPE_OSM_REPORT = 40003,
    PKT_TYPE_OSM_AUTH_REQUEST = 40011,
    PKT_TYPE_OSM_AUTH_REPLY = 40012,
} PacketType;
#define PKT_TYPE_REQUEST(type) (type & 0x01)
#define PKT_TYPE_REPLY(type) (type & 0x01 == 0)
#define PKT_TYPE_ENTITY_GROUP(type) (type/PKT_TYPE_ENTITY_GROUP_SIZE) 
#define PKT_TYPE_ENTITY_GROUP_WEB(type) \
            (PKT_TYPE_ENTITY_GROUP(type) == LY_ENTITY_WEB)
#define PKT_TYPE_ENTITY_GROUP_CLC(type) \
            (PKT_TYPE_ENTITY_GROUP(type) == LY_ENTITY_CLC)
#define PKT_TYPE_ENTITY_GROUP_NODE(type) \
            (PKT_TYPE_ENTITY_GROUP(type) == LY_ENTITY_NODE)
#define PKT_TYPE_ENTITY_GROUP_OSM(type) \
            (PKT_TYPE_ENTITY_GROUP(type) == LY_ENTITY_INSTANCE)


/*
** Node status can be set/get by web, clc and node
** Node status is recorded in db as well
*/
typedef enum NodeStatus_t {
    NODE_STATUS_UNKNOWN = 0,
    NODE_STATUS_UNINITIALIZED = 1,
    NODE_STATUS_INITIALIZED = 2,
    NODE_STATUS_UNAUTHENTICATED = 4,
    NODE_STATUS_AUTHENTICATING = 5,
    NODE_STATUS_AUTHENTICATED = 6,
    NODE_STATUS_UNREGISTERED = 7,
    NODE_STATUS_REGISTERING = 8,
    NODE_STATUS_REGISTERED = 9,
    NODE_STATUS_OFFLINE = 20,
    NODE_STATUS_ONLINE = 21,
    NODE_STATUS_READY = 31,
    NODE_STATUS_BUSY = 32,
    NODE_STATUS_CHECK = 33,
    NODE_STATUS_ERROR = 34,
} NodeStatus;

/*
** Domain status of instance entities
*/
typedef enum DomainStatus_t {
    DOMAIN_S_UNKNOWN = 0,
    DOMAIN_S_NEW = 1,       /* new domain that hasn't run once */
    DOMAIN_S_STOP = 2,      /* domain has run at least once, but now stopped */
    DOMAIN_S_START = 3,     /* domain started by hypervisor */
    DOMAIN_S_RUNNING = 4,   /* domain osm has connected clc */
    DOMAIN_S_SERVING = 5,   /* domain osm web is running */
    DOMAIN_S_SUSPEND = 9,
    DOMAIN_S_DELETE = 100,
    DOMAIN_S_NEED_QUERY = 245, /* domain status needs to be queryed */
    DOMAIN_S_NOT_EXIST = 255,
} DomainStatus;

/*
** OS Manager status
*/
typedef enum OSMStatus_t {
    OSM_STATUS_UNKNOWN = 0,
    OSM_STATUS_INIT = 2,
    OSM_STATUS_UNAUTHENTICATED = 4,
    OSM_STATUS_AUTHENTICATING = 5,
    OSM_STATUS_AUTHENTICATED = 6,
    OSM_STATUS_UNREGISTERED = 7,
    OSM_STATUS_REGISTERING = 8,
    OSM_STATUS_REGISTERED = 9,
    OSM_STATUS_APP_UNKNOWN = 100,
    OSM_STATUS_APP_RUNNING = 101,
    OSM_STATUS_APP_STOPPED = 102,
} OSMStatus;

/*
** other contants of system info
*/
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

typedef enum StorageMethod_t {
    STORAGE_NONE = 0,
    STORAGE_NFS,
    STORAGE_ISCSI,
} StorageMethod;

typedef enum XMLResponseDataType_t {
    DATA_INSTANCE_INFO = 1,
    DATA_NODE_INFO = 2,
} XMLResponseDataType;

/*
** common data structure for instance control to node 
*/
typedef struct NodeCtrlInstance_t {
    int   req_id;         /* same as job id */
    int   req_action;     /* see LYAction */
    int   ins_id;         /* unique instance table id */
    int   ins_status;     /* status in db, see DomainStatus */
    char *ins_name;
    int   ins_vcpu;
    int   ins_mem;
    int   ins_extsize;
    char *ins_mac;
    char *ins_ip;
    char *ins_domain;     /* domain name used by libvirt */
    char *ins_json;
    int   app_id;
    char *app_name;
    char *app_uri;
    char *app_checksum;
    char *osm_clcip;
    int   osm_clcport;
    int   osm_tag;
    char *osm_secret;
    char *osm_json;
    char *storage_ip;
    int   storage_method;
    char *storage_parm;
    int   reply;                 /* flags about what kind of result to be returned */
} NodeCtrlInstance;

/* flags used by InstanceCtrl result field */
#define LUOYUN_REQUEST_REPLY_RESULT 0x01
#define LUOYUN_REQUEST_REPLY_STATUS 0x02

/*
** common data structure for node register info
*/
typedef struct NodeInfo_t {
    unsigned int status;
    unsigned int hypervisor;
    unsigned int storage_total;
    unsigned int storage_free;
    unsigned int mem_max;
    unsigned int mem_vlimit;
    unsigned int mem_free;
    unsigned int mem_commit;
    unsigned int cpu_max;
    unsigned int cpu_vlimit;
    unsigned int cpu_commit;
    unsigned int cpu_mhz;
    unsigned int cpu_arch;          /* cpu arch */
    char *cpu_model;
    char *host_name;
    char *host_ip;                    /* eg 192.168.0.1 */
    int   host_tag;
    unsigned int load_average;
} NodeInfo;

/*
** common data structure for authentication info
*/
#define LUOYUN_AUTH_DATA_LEN 40
#pragma pack(1)
typedef struct AuthInfo_t {
    int tag;
    int8_t data[LUOYUN_AUTH_DATA_LEN];
} AuthInfo;
#pragma pack()

/*
** common data structure for instance info
*/
typedef struct InstanceIfStat_t {
    unsigned long rx_bytes;
    unsigned long rx_pkts;
    unsigned long tx_bytes;
    unsigned long tx_pkts;
} InstanceIfStat;

typedef struct InstanceInfo_t {
    int id;
    int status;
    char *ip;
    int gport; /* graphices port */
    InstanceIfStat netstat[2];
} InstanceInfo;

/*
** common data structure for OS manager register info
*/
typedef struct OSMInfo_t {
    int tag;
    int status;
    char *ip;
} OSMInfo;

/*
** common data structure for reply, used for generating xml responses
*/
typedef struct LYReply_t {
   int req_id;
   int from;
   int to;
   int status; /* see LYActionStatus */
   char * msg; /* readable string for status */
   void * data; /* reply specific data */
} LYReply;

/*
** common data structure for report, used for generating/receiving xml reports
*/
typedef struct LYReport_t {
   int from;
   int to;
   int status;
   char * msg;
   void * data; /* report specific data */
} LYReport;

/* helper functions */
void luoyun_node_ctrl_instance_print(NodeCtrlInstance * ci);
void luoyun_node_ctrl_instance_cleanup(NodeCtrlInstance * ci);
NodeCtrlInstance * luoyun_node_ctrl_instance_copy(NodeCtrlInstance * ci);
void luoyun_node_info_print(NodeInfo * nf);
void luoyun_node_info_cleanup(NodeInfo * nf);
void luoyun_instance_info_print(InstanceInfo *ii);
void luoyun_instance_info_cleanup(InstanceInfo *ii);
void luoyun_osm_info_print(OSMInfo *ii);
void luoyun_osm_info_cleanup(OSMInfo *ii);

#endif
