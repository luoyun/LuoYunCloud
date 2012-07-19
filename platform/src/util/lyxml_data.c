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

#include "lyxml.h"

#define LUOYUN_XML_DATA_MAX     2048

#define __LUOYUN_XML_DATA_PREPARE(flag, buf, size) \
{\
    flag = 1;\
    if (buf == NULL || size == 0) {\
        size = LUOYUN_XML_DATA_MAX;\
        buf = malloc(size);\
        caller_buf_flag = 0;\
    }\
    if (buf == NULL) {\
        free(buf);\
        return NULL;\
    }\
}

#define __LUOYUN_XML_DATA_RETURN(flag, buf, len) \
{\
    if (flag || len > LUOYUN_XML_DATA_MAX/2)\
        return buf;\
    char * ptr = realloc(buf, len+1);\
    if (ptr == NULL) {\
        free(buf);\
        return NULL;\
    }\
    ptr[len] = '\0';\
    return ptr;\
}

/*
** Join request xml template
*/
#define LUOYUN_XML_DATA_JOIN \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<request id=\"%d\" action=\"join\">"\
    "<reply required=\"no\"/>"\
    "<parameters>"\
      "<host>%s</host>"\
      "<port>%d</port>"\
    "</parameters>"\
  "</request>"\
"</" LYXML_ROOT ">"

#if 1
char * lyxml_data_join(int id, char * host, int port,
                       char * buf, unsigned int size)
{
    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)
    int len = snprintf(buf, size, LUOYUN_XML_DATA_JOIN, 
                       LY_ENTITY_CLC, 
                       LY_ENTITY_NODE, 
                       id, (char *)(BAD_CAST host), port);
    if (len < 0 || len >= size)
        return NULL;
    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

#else

char * lyxml_data_join(int id, char * host, int port,
                       char * buf, unsigned int size)
{
    int caller_buf_flag = 1;
    if (buf == NULL || size == 0) {
        size = LUOYUN_XML_DATA_MAX;
        buf = malloc(size);
        caller_buf_flag = 0;
    }
    if (buf == NULL)
        return NULL;

    int len = snprintf(buf, size, LUOYUN_XML_DATA_JOIN, 
                       LY_ENTITY_CLC, 
                       LY_ENTITY_NODE, 
                       id, (char *)(BAD_CAST host), port);
    if (len < 0 || len >= size){
        free(buf);
        return NULL;
    }

    if (caller_buf_flag || len > LUOYUN_XML_DATA_MAX/2)
        return buf;

    unsigned char * ptr = realloc(buf, len+1);
    if (ptr == NULL) {
        free(buf);
        return NULL;
    }
    ptr[len] = '\0';
    return ptr;
}

#endif

/*
** Node register request xml template
*/
#define LUOYUN_XML_DATA_NODE_REGISTER \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<request id=\"%d\" action=\"%d\">"\
    "<reply required=\"yes\">"\
      "<result/>"\
    "</reply>"\
    "<parameters>"\
      "<status>%d</status>"\
      "<hypervisor>%d</hypervisor>"\
      "<host>"\
        "<tag>%d</tag>"\
        "<name>%s</name>"\
        "<ip>%s</ip>"\
      "</host>"\
      "<memory>"\
        "<total>%u</total>"\
        "<free>%u</free>"\
        "<commit>%u</commit>"\
      "</memory>"\
      "<cpu>"\
        "<arch>%d</arch>"\
        "<model>%s</model>"\
        "<mhz>%d</mhz>"\
        "<max>%d</max>"\
        "<commit>%d</commit>"\
      "</cpu>"\
      "<storage>"\
        "<total>%u</total>"\
        "<free>%u</free>"\
      "</storage>"\
      "<load>"\
        "<average>%d</average>"\
      "</load>"\
    "</parameters>"\
  "</request>"\
"</" LYXML_ROOT ">"

char * lyxml_data_node_register(NodeInfo * ni, char * buf, unsigned int size)
{
    if (ni == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_NODE_REGISTER, 
                       LY_ENTITY_NODE, 
                       LY_ENTITY_CLC, 
                       lynode_new_request_id(),
                       LY_A_CLC_REGISTER_NODE,
                       ni->status,
                       ni->hypervisor,
                       ni->host_tag,
                       ni->host_name ? (char *)(BAD_CAST ni->host_name) : "",
                       ni->host_ip ? (char *)(BAD_CAST ni->host_ip) : "",
                       ni->mem_max, ni->mem_free, ni->mem_commit,
                       ni->cpu_arch,
                       ni->cpu_model ? (char *)(BAD_CAST ni->cpu_model) : "",
                       ni->cpu_mhz, ni->cpu_max, ni->cpu_commit,
                       ni->storage_total, ni->storage_free,
                       ni->load_average);
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** Node authentication info response xml template
*/
#define LUOYUN_XML_DATA_REPLY_AUTH_INFO \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<response id=\"%d\" status=\"%d\">"\
    "<data>"\
      "<tag>%d</tag>"\
      "<secret>%s</secret>"\
    "</data>"\
  "</response>"\
"</" LYXML_ROOT ">"

char * lyxml_data_reply_auth_info(LYReply * reply,
                                  char * buf, unsigned int size)
{
    if (reply == NULL || reply->data == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    AuthInfo * ai = reply->data;
    int len = snprintf(buf, size, LUOYUN_XML_DATA_REPLY_AUTH_INFO,
                       reply->from, reply->to,
                       reply->req_id, reply->status,
                       ai->tag, 
                       ai->data[0] != '\0' ? (char *)(BAD_CAST ai->data) : "");
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}


/*
** Node info request xml template
*/
#define LUOYUN_XML_DATA_NODE_INFO \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<request id=\"%d\" action=\"%d\">"\
    "<reply required=\"yes\">"\
      "<result/>"\
    "</reply>"\
  "</request>"\
"</" LYXML_ROOT ">"

char * lyxml_data_node_info(int req_id, char * buf, unsigned int size)
{
    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_NODE_INFO,
                       LY_ENTITY_CLC, LY_ENTITY_NODE,
                       req_id, LY_A_NODE_QUERY);
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** Node info response xml template
*/
#define LUOYUN_XML_DATA_REPLY_NODE_INFO \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<response id=\"%d\" status=\"%d\">"\
    "<data type=\"%d\">"\
      "<status>%d</status>"\
      "<cpu>"\
        "<commit>%d</commit>"\
      "</cpu>"\
      "<memory>"\
        "<free>%u</free>"\
        "<commit>%u</commit>"\
      "</memory>"\
      "<storage>"\
        "<free>%u</free>"\
      "</storage>"\
      "<load>"\
        "<average>%d</average>"\
      "</load>"\
    "</data>"\
  "</response>"\
"</" LYXML_ROOT ">"

char * lyxml_data_reply_node_info(LYReply * reply, char * buf, unsigned int size)
{
    if (reply == NULL || reply->data == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    NodeInfo * ni = reply->data; 
    int len = snprintf(buf, size, LUOYUN_XML_DATA_REPLY_NODE_INFO, 
                       reply->from, reply->to,
                       reply->req_id, reply->status,
                       DATA_NODE_INFO,
                       ni->status,
                       ni->cpu_commit,
                       ni->mem_free,
                       ni->mem_commit,
                       ni->storage_free,
                       ni->load_average);
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** instance run request xml template
*/
#define LUOYUN_XML_DATA_INSTANCE_RUN \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<request id=\"%d\" action=\"%d\">"\
    "<reply required=\"yes\">"\
      "<status/>"\
      "<result/>"\
    "</reply>"\
    "<parameters>"\
      "<instance id=\"%d\" status=\"%d\">"\
        "<name>%s</name>"\
        "<vcpu>%d</vcpu>"\
        "<memory>%d</memory>"\
        "<mac>%s</mac>"\
        "<ip>%s</ip>"\
        "<domain>%s</domain>"\
      "</instance>"\
      "<appliance id=\"%d\">"\
        "<name>%s</name>"\
        "<uri>%s</uri>"\
        "<checksum>%s</checksum>"\
      "</appliance>"\
      "<osmanager>"\
        "<clc>"\
          "<ip>%s</ip>"\
          "<port>%d</port>"\
        "</clc>"\
        "<tag>%d</tag>"\
        "<secret>%s</secret>"\
        "<json>%s</json>"\
      "</osmanager>"\
      "<storage>"\
        "<ip>%s</ip>"\
        "<method>%d</method>"\
        "<parm>%s</parm>"\
      "</storage>"\
    "</parameters>"\
  "</request>"\
"</" LYXML_ROOT ">"

char * lyxml_data_instance_run(NodeCtrlInstance * ii, char * buf, unsigned int size)
{
    if (ii == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_INSTANCE_RUN,
                       LY_ENTITY_CLC, 
                       LY_ENTITY_NODE, 
                       ii->req_id, ii->req_action, ii->ins_id, ii->ins_status,
                       ii->ins_name ? (char *)(BAD_CAST ii->ins_name) : "",
                       ii->ins_vcpu, ii->ins_mem,
                       ii->ins_mac ? (char *)(BAD_CAST ii->ins_mac) : "",
                       ii->ins_ip ? (char *)(BAD_CAST ii->ins_ip) : "",
                       ii->ins_domain ? (char *)(BAD_CAST ii->ins_domain) : "",
                       ii->app_id,
                       ii->app_name ? (char *)(BAD_CAST ii->app_name) : "",
                       ii->app_uri ? (char *)(BAD_CAST ii->app_uri) : "",
                       ii->app_checksum ? (char *)(BAD_CAST ii->app_checksum) : "",
                       ii->osm_clcip ? (char *)(BAD_CAST ii->osm_clcip) : "",
                       ii->osm_clcport, ii->osm_tag,
                       ii->osm_secret ? (char *)(BAD_CAST ii->osm_secret) : "",
                       ii->osm_json ? (char *)(BAD_CAST ii->osm_json) : "",
                       ii->storage_ip ? (char *)(BAD_CAST ii->storage_ip) : "",
                       ii->storage_method,
                       ii->storage_parm ? (char *)(BAD_CAST ii->storage_parm) : "");
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** instance stop request xml template
*/
#define LUOYUN_XML_DATA_INSTANCE_STOP \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<request id=\"%d\" action=\"%d\">"\
    "<reply required=\"yes\">"\
      "<result/>"\
    "</reply>"\
    "<parameters>"\
      "<instance id=\"%d\">"\
        "<domain>%s</domain>"\
      "</instance>"\
    "</parameters>"\
  "</request>"\
"</" LYXML_ROOT ">"

char * lyxml_data_instance_stop(NodeCtrlInstance * ii, char * buf, unsigned int size)
{
    if (ii == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_INSTANCE_STOP,
                       LY_ENTITY_CLC, 
                       LY_ENTITY_NODE, 
                       ii->req_id, ii->req_action, ii->ins_id,
                       ii->ins_domain ? (char *)(BAD_CAST ii->ins_domain) : "");
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** other instance request xml template
*/
#define LUOYUN_XML_DATA_INSTANCE_OTHER \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<request id=\"%d\" action=\"%d\">"\
    "<reply required=\"yes\">"\
      "<result/>"\
    "</reply>"\
    "<parameters>"\
      "<instance id=\"%d\">"\
        "<domain>%s</domain>"\
      "</instance>"\
    "</parameters>"\
  "</request>"\
"</" LYXML_ROOT ">"

char * lyxml_data_instance_other(NodeCtrlInstance * ii, char * buf, unsigned int size)
{
    if (ii == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_INSTANCE_OTHER,
                       LY_ENTITY_CLC, 
                       LY_ENTITY_NODE, 
                       ii->req_id, ii->req_action, ii->ins_id,
                       ii->ins_domain ? (char *)(BAD_CAST ii->ins_domain) : "");
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** instance register request xml template
*/
#define LUOYUN_XML_DATA_INSTANCE_REGISTER \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"instance\"/>"\
  "<to entity=\"clc\"/>"\
  "<response id=\"%d\" action=\"register\">"\
    "<reply required=\"yes\">"\
      "<result/>"\
    "</reply>"\
    "<parameters>"\
      "<host>"\
        "<name>%s</name>"\
        "<ip>%s</ip>"\
      "</host>"\
    "</parameters>"\
  "</response>"\
"</" LYXML_ROOT ">"

char * lyxml_data_instance_register(int id, char * hostname, char * ip,
                                    char * buf, unsigned int size)
{
    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_INSTANCE_REGISTER,
                       id, 
                       (char *)(BAD_CAST hostname),
                       (char *)(BAD_CAST ip));
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** reply xml template
*/
#define LUOYUN_XML_DATA_REPLY \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<response id=\"%d\" status=\"%d\">"\
    "<result>%s</result>"\
  "</response>"\
"</" LYXML_ROOT ">"

char * lyxml_data_reply(LYReply * reply, char * buf, unsigned int size)
{
    if (reply == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_REPLY,
                       reply->from, reply->to, reply->req_id,
                       reply->status,
                       reply->msg ? (char *)(BAD_CAST reply->msg) : "");
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** instance info query xml template
*/
#define LUOYUN_XML_DATA_INSTANCE_INFO \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<response id=\"%d\" status=\"%d\">"\
    "<data type=\"%d\">"\
      "<id>%d</id>"\
      "<status>%d</status>"\
      "<ip>%s</ip>"\
    "</data>"\
  "</response>"\
"</" LYXML_ROOT ">"

char * lyxml_data_reply_instance_info(LYReply * reply, char * buf,
                                      unsigned int size)
{
    if (reply == NULL || reply->data == NULL)
        return NULL;

    InstanceInfo * ii = reply->data;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_INSTANCE_INFO,
                       reply->from, reply->to, reply->req_id,
                       reply->status,
                       DATA_INSTANCE_INFO,
                       ii->id,
                       ii->status,
                       ii->ip ? (char *)(BAD_CAST ii->ip) : "");
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

/*
** report 
*/
#define LUOYUN_XML_DATA_REPORT \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<report>"\
    "<status>%d</status>"\
    "<message>%s</message>"\
  "</report>"\
"</" LYXML_ROOT ">"

char * lyxml_data_report(LYReport * r, char * buf, unsigned int size)
{
    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    int len = snprintf(buf, size, LUOYUN_XML_DATA_REPORT,
                       r->from, r->to, r->status,
                       r->msg ? (char *)(BAD_CAST r->msg) : "");
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}


/*
** Node info report xml template
*/
#define LUOYUN_XML_DATA_REPORT_NODE_INFO \
"<?xml version=\"1.0\" encoding=\"" LYXML_ENCODING "\"?>"\
"<" LYXML_ROOT ">"\
  "<from entity=\"%d\"/>"\
  "<to entity=\"%d\"/>"\
  "<report>"\
    "<resource>"\
      "<cpu>"\
        "<commit>%d</commit>"\
      "</cpu>"\
      "<memory>"\
        "<free>%u</free>"\
        "<commit>%u</commit>"\
      "</memory>"\
      "<storage>"\
        "<free>%u</free>"\
      "</storage>"\
      "<load>"\
        "<average>%d</average>"\
      "</load>"\
    "</resource>"\
  "</report>"\
"</" LYXML_ROOT ">"

char * lyxml_data_report_node_info(LYReport * r, char * buf, unsigned int size)
{
    if (r == NULL || r->data == NULL)
        return NULL;

    int caller_buf_flag = 1;
    __LUOYUN_XML_DATA_PREPARE(caller_buf_flag, buf, size)

    NodeInfo * ni = r->data; 
    int len = snprintf(buf, size, LUOYUN_XML_DATA_REPORT_NODE_INFO, 
                       r->from, r->to,
                       ni->cpu_commit,
                       ni->mem_free,
                       ni->mem_commit,
                       ni->storage_free,
                       ni->load_average);
    if (len < 0 || len >= size)
        return NULL;

    __LUOYUN_XML_DATA_RETURN(caller_buf_flag, buf, len)
}

