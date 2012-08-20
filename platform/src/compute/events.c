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
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <ifaddrs.h>            /* getifaddrs */
#include <unistd.h>             /* gethostname */
#include <netdb.h>              /* struct hostent */
#include <errno.h>

#include "../util/logging.h"
#include "../util/lyutil.h"
#include "../util/lyauth.h"
#include "../util/lyxml.h"
#include "domain.h"
#include "handler.h"
#include "node.h"
#include "events.h"

/* not pretty! debugging only */
static void __print_recv_buf(char *buf)
{
    int i;
    for (i=0; i<8; i++)
        logsimple("%02x ", buf[i]);
    logsimple("\n");
    LYPacketHeader h = *(LYPacketHeader *)buf;
    int type = h.type;
    int len = h.length;
    logsimple("type = %d, length = %d\n", type, len);
}

/* process node query request */
static int __process_node_query(int req_id)
{
    LYReply r;
    r.req_id = req_id;
    r.from = LY_ENTITY_NODE;
    r.to = LY_ENTITY_CLC;
    if (ly_node_info_update() < 0)
        r.status = LY_S_FINISHED_FAILURE;
    else
        r.status = LY_S_FINISHED_SUCCESS;
    r.msg = NULL;
    r.data = g_c->node;
    logdebug(_("sending node query reply...\n"));
    char * xml = lyxml_data_reply_node_info(&r, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    int ret = ly_packet_send(g_c->wfd, PKT_TYPE_CLC_NODE_CONTROL_REPLY,
                             xml, strlen(xml));
    free(xml);

    /* clear one time error/check status */
    if (g_c->state == NODE_STATUS_CHECK ||
        g_c->state == NODE_STATUS_ERROR)
        g_c->state = NODE_STATUS_READY;

    return ret;
}

/* process xml request */
static int __process_xml_request(xmlDocPtr doc, xmlNodePtr node)
{
    /* get id attributes */
    char * str = (char *)xmlGetProp(node, (const xmlChar *)"id");
    if (str == NULL) {
        logerror(_("error processing xml node(%s, %d)\n"),
                   __func__, __LINE__);
        return -1;
    }
    int id = atoi(str);
    free(str);

    /* get action attributes */
    str = (char *)xmlGetProp(node, (const xmlChar *)"action");
    if (str == NULL) {
        logerror(_("error processing xml node(%s, %d)\n"),
                   __func__, __LINE__);
        return -1;
    }
    int action = atoi(str);
    free(str);

    loginfo(_("process request %d(id=%d)\n"), action, id);

    if (action == LY_A_NODE_QUERY)
        return __process_node_query(id);

    /* others are instance control requests */
    NodeCtrlInstance ci;
    bzero(&ci, sizeof(NodeCtrlInstance));
    ci.req_id = id;
    ci.req_action = action;

    /* Create xpath evaluation context */
    xmlXPathContextPtr xpathCtx = xmlXPathNewContext(doc);
    if(xpathCtx == NULL) {
        logerror(_("unable to create new XPath context %s, %d\n"),
                   __func__, __LINE__);
        return -1;
    }
    int ret = -1;
    if (xml_xpath_exist_from_ctx(xpathCtx,
                        "/" LYXML_ROOT "/request/reply/result"))
        ci.reply |= LUOYUN_REQUEST_REPLY_RESULT;
    if (xml_xpath_exist_from_ctx(xpathCtx, 
                        "/" LYXML_ROOT "/request/reply/status"))
        ci.reply |= LUOYUN_REQUEST_REPLY_STATUS;
    str = xml_xpath_prop_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance", "id");
    if (str == NULL)
        goto out;
    ci.ins_id = atoi(str);
    free(str);
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance/name");
    if (str != NULL) {
        ci.ins_name = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance/domain");
    if (str == NULL)
        goto out;
    ci.ins_domain = str;
    str = xml_xpath_prop_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance", "status");
    if (str != NULL) {
        ci.ins_status = atoi(str);
        free(str);
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance/vcpu");
    if (str != NULL) {
        ci.ins_vcpu = atoi(str);
        free(str);
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance/memory");
    if (str != NULL) {
        ci.ins_mem = atoi(str);
        free(str);
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance/mac");
    if (str != NULL) {
        ci.ins_mac = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/instance/ip");
    if (str != NULL) {
        ci.ins_ip = str;
    }
    str = xml_xpath_prop_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/appliance", "id");
    if (str != NULL) {
        ci.app_id = atoi(str);
        free(str);
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/appliance/name");
    if (str != NULL) {
        ci.app_name = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/appliance/uri");
    if (str != NULL) {
        ci.app_uri = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/appliance/checksum");
    if (str != NULL) {
        ci.app_checksum = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/osmanager/clc/ip");
    if (str != NULL) {
        ci.osm_clcip = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/osmanager/clc/port");
    if (str != NULL) {
        ci.osm_clcport = atoi(str);
        free(str);
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/osmanager/tag");
    if (str != NULL) {
        ci.osm_tag = atoi(str);
        free(str);
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/osmanager/secret");
    if (str != NULL) {
        ci.osm_secret = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/osmanager/json");
    if (str != NULL) {
        ci.osm_json = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/storage/ip");
    if (str != NULL) {
        ci.storage_ip = str;
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/storage/method");
    if (str != NULL) {
        ci.storage_method = atoi(str);
    }
    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/request/parameters/storage/parm");
    if (str != NULL) {
        ci.storage_parm = str;
    }

    if (g_c->config.debug)
        luoyun_node_ctrl_instance_print(&ci);
    ret = ly_handler_instance_control(&ci);

out:
    luoyun_node_ctrl_instance_cleanup(&ci);
    xmlXPathFreeContext(xpathCtx);
    return ret;
}

/* process xml response */
static int __process_xml_response(xmlDoc *doc, xmlNode * node)
{
    /* simplified response processing, */
    /* only node register reply is expected, id is not used */

    /* get response status */
    char * str = (char *)xmlGetProp(node, (const xmlChar *)"status");
    if (str == NULL) {
        logerror(_("error processing xml node(%s, %d)\n"),
                   __func__, __LINE__);
        return -1;
    }
    int status = atoi(str);
    free(str);
    loginfo(_("process response status %d\n"), status);

    NodeInfo * nf = g_c->node;
    AuthConfig *ac = &g_c->auth;

    if (status == LY_S_REGISTERING_INIT) {
        loginfo(_("node waiting to be initialized\n"));
        g_c->state = NODE_STATUS_UNINITIALIZED;
        return 0;
    }
    else if (status == LY_S_REGISTERING_DONE_SUCCESS) {
        loginfo(_("node registered successfully\n"));
        g_c->state = NODE_STATUS_REGISTERED;
        ly_sysconf_save();
        return 0;
    }
    else if (status == LY_S_REGISTERING_REINIT) {
        loginfo(_("node registering failed. re-registering required\n"));
        nf->host_tag = -1;
        if (ac->secret) {
            free(ac->secret);
            ac->secret = NULL;
        }
        g_c->state = NODE_STATUS_UNINITIALIZED;
        return 0;
    }
    else if (status != LY_S_REGISTERING_CONFIG) {
        logwarn(_("unexpected register response. ignored\n"));
        return 0;
    }

    loginfo(_("Auth info received. node being initialized\n"));

    /* Create xpath evaluation context */
    xmlXPathContextPtr xpathCtx = xmlXPathNewContext(doc);
    if (xpathCtx == NULL) {
        logerror(_("unable to create new XPath context %s, %d\n"),
                 __func__, __LINE__);
        return -1;
    }

    str = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/response/data/tag");
    if (str == NULL) 
        goto failed;
    nf->host_tag = atoi(str);
    free(str);

    if (ac->secret) {
        free(ac->secret);
        ac->secret = NULL;
    }
    ac->secret = xml_xpath_text_from_ctx(xpathCtx,
                         "/" LYXML_ROOT "/response/data/secret");
    if (ac->secret == NULL) 
        goto failed;

    g_c->state = NODE_STATUS_INITIALIZED;

    xmlXPathFreeContext(xpathCtx);

    /* start authetication */
    if (ly_register_node() != 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    return 0;

failed:
    xmlXPathFreeContext(xpathCtx);
    return -1;
}

/* process xml packet */
static int __process_work_xml(char *xml)
{
    int ret = 0;
    xmlDoc *doc = xml_doc_from_str(xml);
    if (doc == NULL) {
        logerror(_("error: could not parse xml string.\n"));
        logdebug("%s\n", xml);
        return -255;
    }
    logdebug("%s\n", xml);
    xmlNode * node = xmlDocGetRootElement(doc);
    if (node == NULL || strcmp((char *)node->name, LYXML_ROOT) != 0) {
        logwarn(_("error: xml string not for .\n"), LYXML_ROOT);
        return 0;
    }
    node = node->children;

    for (; node; node = node->next) {
        if (node->type == XML_ELEMENT_NODE) {
            logdebug(_("xml node %s\n"), node->name);
            if (strcmp((char *)node->name, "response") == 0 ) {
                if (__process_xml_response(doc, node) < 0) {
                    ret = -1;
                    break;
                }
            }
            else if (strcmp((char *)node->name, "request") == 0 ) {
                if (__process_xml_request(doc, node) < 0) {
                    ret = -1;
                    break;
                }
            }
            /* other nodes ignored */
        }
    }
    xmlFreeDoc(doc);
    return ret;
}

/* process authentication packets */
static int __process_work_authtication(int is_reply, void * buf, int len)
{
    if (buf == NULL || len != sizeof(AuthInfo)) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    AuthInfo * ai = buf;

    int ret;
    AuthConfig * ac = &g_c->auth;

    if (is_reply) {
        if (g_c->state != NODE_STATUS_AUTHENTICATING) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        ret = lyauth_verify(ac, ai->data, LUOYUN_AUTH_DATA_LEN);
        if (ret < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        if (ret) {
            loginfo(_("chanllenge verification passed.\n"));
            g_c->state = NODE_STATUS_AUTHENTICATED;
        }
        else {
            logwarn(_("chanllenge verification failed.\n"));
            g_c->state = NODE_STATUS_UNAUTHENTICATED;
            return 1;
        }
            
        return 0;
    }

    ret = lyauth_answer(ac, ai->data, LUOYUN_AUTH_DATA_LEN);
    if (ret < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* send answer back */
    if (ly_packet_send(g_c->wfd, PKT_TYPE_NODE_AUTH_REPLY,
                       ai, sizeof(AuthInfo)) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* authetication completed */
    if (ly_register_node() != 0)
        logerror(_("failed registering node in %s\n"), __func__);
    return 0;
}

/* process unicast join request */
static int __process_work_join(char * buf)
{
    if (g_c->node->host_tag > 0)
        g_c->state = NODE_STATUS_INITIALIZED;
    else
        g_c->state = NODE_STATUS_UNINITIALIZED;
    if (ly_register_node() != 0)
        logerror(_("failed registering node in %s\n"), __func__);
    return 0;
}

/* process echo request */
static int __process_work_echo(char * buf, int size)
{
    logdebug(_("sending echo reply ...\n"));
    logdebug(_("%s\n"), buf);
    return ly_packet_send(g_c->wfd, PKT_TYPE_TEST_ECHO_REPLY, buf, size);
}

/*
** work socket EPOLLIN event processing
** return -1 : error
**         0 : success, nothing expected to be followed
**         1 : success, socket closed
**/
int ly_epoll_work_recv(void)
{
    if (g_c == NULL || g_c->wfd < 0)
        return -255;

    LYPacketRecv * pkt = &g_c->wfd_pkt;
    if (pkt == NULL)
        return -255;

    int size;
    void * buf = ly_packet_buf(pkt, &size);
    if (buf == NULL) {
        logerror(_("ly_packet_buf returns NULL buffer. close socket\n"));
        return 1;
    }
    if (size == 0) {
        logerror(_("ly_packet_buf returns 0 size buffer. close socket\n"));
        return 1;
    }

    int ret = recv(g_c->wfd, buf, size, 0);
    if (ret == -1) {
        logerror(_("recv error(%d) in %s. close socket.\n"), errno, __func__);
        return 1;
    }
    else if (ret == 0) {
        /* Maybe the client have closed */
        loginfo(_("recv 0 byte. close socket.\n"));
        return 1;
    }
    logdebug(_("recv %d bytes received\n"), ret);
    if (g_c->config.debug)
        __print_recv_buf(buf);

    while(1) {
        ret = ly_packet_recv(pkt, ret);
        if (ret == 0) {
            /* continue */
            return 0;
        }
        else if (ret < 0) {
            logerror(_("package recv error in %s.\n"), __func__);
            return -1;
        }

        int len; 
        buf = ly_packet_data(pkt, &len);
        int type = ly_packet_type(pkt);
        if (type == PKT_TYPE_JOIN_REQUEST) {
            ret = __process_work_join(buf);
            if (ret < 0)
                logerror(_("string packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_TEST_ECHO_REQUEST) {
            ret = __process_work_echo(buf, len);
            if (ret < 0)
                logerror(_("echo packet process error in %s.\n"), __func__);
        }
        else if (type == PKT_TYPE_NODE_AUTH_REQUEST ||
                 type == PKT_TYPE_NODE_AUTH_REPLY) {
            ret = __process_work_authtication(
                    type == PKT_TYPE_NODE_AUTH_REPLY ? 1 : 0, buf, len);
            if (ret < 0)
                logerror(_("auth packet process error in %s.\n"), __func__);
        }
        else if (PKT_TYPE_ENTITY_GROUP_CLC(type) ||
                 PKT_TYPE_ENTITY_GROUP_NODE(type)) {
            ret = __process_work_xml(buf);
            if (ret < 0)
                logerror(_("xml packet process error in %s.\n"), __func__);
        }
        else {
            logerror(_("unrecognized packet type.\n"));
        }

        if (ly_packet_recv_done(pkt) < 0 || ret < 0) {
            logerror(_("%s return error\n"), __func__);
            return -1;
        }

        if (ret > 0)
            return ret;

        ret = 0; /* continue processing data in buffer */
    }

    return 0;
}

/* register to clc */
int ly_register_node()
{
    if (g_c == NULL || g_c->wfd < 0)
        return -255;

    NodeInfo *nf = g_c->node;
    AuthConfig *ac = &g_c->auth;
    
    if (g_c->state == NODE_STATUS_INITIALIZED) {
        /* request challenging */
        if (lyauth_prepare(ac) < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        
        AuthInfo ai;
        ai.tag = nf->host_tag;
        bzero(ai.data, LUOYUN_AUTH_DATA_LEN);
        strncpy((char *)ai.data, ac->challenge, LUOYUN_AUTH_DATA_LEN);
        if (ly_packet_send(g_c->wfd, PKT_TYPE_NODE_AUTH_REQUEST,
                           &ai, sizeof(AuthInfo)) < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            return -1;
        }
        g_c->state = NODE_STATUS_AUTHENTICATING;
        return 0;
    }

    if (ly_node_info_update() < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    loginfo(_("Send register request...\n"));

    if (g_c->state >= NODE_STATUS_UNAUTHENTICATED &&
        g_c->state >= NODE_STATUS_AUTHENTICATED)
        g_c->state = NODE_STATUS_UNREGISTERED;

    /* build xml string */
    char * xml = lyxml_data_node_register(nf, NULL, 0);
    if (xml == NULL) {
        logerror(_("build register xml request error\n"));
        return -1;
    }
    int size = strlen(xml);
    logdebug(_("xml string(%d):\n%s\n"), size, xml);

    if (ly_packet_send(g_c->wfd, PKT_TYPE_NODE_REGISTER_REQUEST, xml, size) < 0) {
        logerror(_("packet send error(%d, %d)\n"), __LINE__, errno);
        free(xml);
        return -1;
    }

    free(xml);

    if (g_c->state == NODE_STATUS_UNREGISTERED)
        g_c->state = NODE_STATUS_REGISTERING;

    return 0;
}

/* work socket registration */
int ly_epoll_work_register(void)
{
    if (g_c == NULL || g_c->efd < 0)
        return -255;

    if (g_c->wfd >= 0)
        ly_epoll_work_close();

    /* connect to clc */
    int fd = lyutil_connect_to_host(g_c->clc_ip, g_c->clc_port);
    if (fd <= 0) {
        logerror(_("connect_to_host %s %d error.\n"),
                    g_c->clc_ip, g_c->clc_port);
        return -1;
    }

    if (g_c->node_ip == NULL) {
        g_c->node_ip = lyutil_get_local_ip(fd);
        if (g_c->node_ip == NULL) {
            logerror(_("get local ip error in %s\n"), __func__);
            close(fd);
            return -1;
        }
    }

    /* make socket nonblocking */
    int ret = lyutil_make_socket_nonblocking(fd);
    if (ret != 0) {
        logerror(_("Making socket nonblocking error %s"), __func__);
        close(fd);
        return -1;
    }

    /* keep alive */
    if (lyutil_set_keepalive(fd, LY_NODE_KEEPALIVE_INTVL,
                                 LY_NODE_KEEPALIVE_INTVL,
                                 LY_NODE_KEEPALIVE_PROBES) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        close(fd);
        return -1;
    }

    /* prepare packet receive structure */
    ret = ly_packet_init(&g_c->wfd_pkt);
    if (ret < 0 ) {
        logerror(_("ly_packet_init error in  %s\n"), __func__);
        close(fd);
        return ret;
    }

    /* register socket */
    struct epoll_event ev;
    /* ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP; */
    ev.events = EPOLLIN;
    ev.data.fd = fd;
    ret = epoll_ctl(g_c->efd, EPOLL_CTL_ADD, fd, &ev);
    if (ret < 0) {
        logerror(_("Add work socket to epoll error.\n"));
        close(fd);
        ly_packet_cleanup(&g_c->wfd_pkt);
        return ret;
    }

    loginfo(_("Registering work socket(%d).\n"), fd);
    g_c->wfd = fd;
    return 0;
}

static int  __process_mcast_string(char * str, char * ip, int * port)
{
    if (str == NULL || ip == NULL || port == NULL)
        return -255;

    char s[MAX_IP_LEN+20], j[10];
    sprintf(s, "%%9s %%%ds %%d\n", MAX_IP_LEN);
    if (sscanf(str, s, j, ip, port) != 3 || strcmp(j, "join") != 0) {
        logwarn(_("string message unrecoginized at %d.\n"), __LINE__);
        logdebug(str);
        return -1;
    }
    logdebug(_("join %s %d\n"), ip, *port);
    return 0;
}

/* not used */
#if 0
static int  __process_mcast_xml(char * xml, char * ip, int * port)
{
    int ret = -1;
    xmlDoc *doc = xml_doc_from_str(xml);
    if (doc == NULL) {
        logerror(_("error: could not parse xml string.\n%s\n"), xml);
        return -255;
    }
    logdebug("%s\n", xml);
    xmlNode * node = xmlDocGetRootElement(doc);
    if (strcmp((char *)node->name, LYXML_ROOT) != 0) {
        logwarn(_("xml string unrecoginized at %d."), __LINE__);
        goto out;
    }
    node = node->children; 
    for (; node; node = node->next) {
        if (strcmp((char *)node->name, "request") == 0)
            break;
    }
    if (node == NULL) {
        logwarn(_("xml string unrecoginized at %d."), __LINE__);
        goto out;
    }
 
    /* simplified response processing, id is not used */
    char * str = (char *)xmlGetProp(node, (const xmlChar *)"id");
    if (str == NULL) {
        logwarn(_("xml string unrecoginized at %d."), __LINE__);
        goto out;
    }
    int id = atoi(str);
    free(str);
    loginfo(_("request id %d\n"), id);
    str = (char *)xmlGetProp(node, (const xmlChar *)"action");
    if (str == NULL) {
        logwarn(_("xml string unrecoginized at %d."), __LINE__);
        goto out;
    }
    if (strcmp(str, "join") != 0) { 
        logwarn(_("xml string unrecoginized at %d."), __LINE__);
        free(str);
        goto out;
    }
    loginfo(_("request action %s\n"), str);
    free(str);
 
    xmlXPathContextPtr xpathCtx = xmlXPathNewContext(doc);
    if(xpathCtx == NULL) {
        logerror(_("unable to create new XPath context %s, %d\n"),
                   __func__, __LINE__);
        goto out;
    }
    str = xml_xpath_text_from_ctx(xpathCtx, "/luoyun/request/parameters/host");
    if (str == NULL) {
        logerror(_("xml element host not found\n"));
        free(str);
        xmlXPathFreeContext(xpathCtx);
        goto out;
    }
    strcpy(ip, str);
    free(str);
    str = xml_xpath_text_from_ctx(xpathCtx, "/luoyun/request/parameters/port");
    if (str == NULL) {
        logerror(_("xml element port not found\n"));
        free(str);
        xmlXPathFreeContext(xpathCtx);
        goto out;
    }
    logdebug("%s\n", str);
    *port = atoi(str);
    free(str);
    loginfo(_("join %s %d\n"), ip, *port);

    ret = 0;
out:
    xmlFreeDoc(doc);
    return ret;
}
#endif

/* 
** receive/check mcast data
** upon successful return, clc_ip/clc_port/host_ip are recorded in g_c
** return -1 : error
**         0 : success, nothing expected to be followed
**         1 : success, registering should be followed
*/
int ly_epoll_mcast_recv()
{
    if (g_c == NULL || g_c->mfd < 0 || g_c->mfd_cmsg == NULL)
        return -255;

    struct msghdr msg;
    struct iovec s; 
    int size;
    s.iov_base = ly_packet_buf(&g_c->mfd_pkt, &size);
    if (s.iov_base == NULL) {
        logerror(_("packet buffer error %s(line %d)\n"), __func__, __LINE__);
        return -255;
    }
    s.iov_len = size;

    msg.msg_name = NULL;
    msg.msg_namelen = 0;
    msg.msg_iov = &s;
    msg.msg_iovlen = 1;
    msg.msg_control = g_c->mfd_cmsg;
    msg.msg_controllen = g_c->mfd_cmsg_size;
    int datalen = recvmsg(g_c->mfd, &msg, 0);
    if (datalen < 0) {
        logerror(_("recvmsg returns error in %s\n"), __func__);
        return -1;
    }
    logdebug("recvmsg %d bytes received\n", datalen);
    /* __print_recv_buf(s.iov_base); */

    char ip[MAX_IP_LEN];
    int port = 0;
    int ret = ly_packet_recv(&g_c->mfd_pkt, datalen);
    if (ret == 0) {
        logerror(_("mcast packet partially received. ignore.\n"));
        ly_packet_recv_done(&g_c->mfd_pkt);
        return 0;
    }
    else if (ret < 0) {
        logerror(_("ly_packet_recv error(%d)\n"), ret);
    }
    else if (ly_packet_type(&g_c->mfd_pkt) == PKT_TYPE_JOIN_REQUEST) {
        ret = __process_mcast_string(ly_packet_data(&g_c->mfd_pkt, NULL), ip, &port);
        if (ret < 0)
            logerror(_("string packet process error in %s.\n"), __func__);
    }
    else {
        logwarn(_("unrecognized mcast msg received.\n"));
        ret = -1;
    }
    if (ly_packet_recv_done(&g_c->mfd_pkt) < 0 || ret < 0)
        return -1;

    char localip[MAX_IP_LEN];
    if (msg.msg_controllen > 0) {
        struct cmsghdr *h = msg.msg_control;
        /*
        logdebug("%d %d %d %s %p %p\n", h->cmsg_len, h->cmsg_type, h->cmsg_level,
                                        h->cmsg_type == IP_PKTINFO ? "yes":"no",
                                        h, (char *)((char*)h+sizeof(*h)));
        */
        if (h->cmsg_type != IP_PKTINFO) {
            logwarn(_("unrecognized mcast msg control data received %d\n"),
                       h->cmsg_type); 
            return -1;
        }
        struct in_pktinfo * i = (struct in_pktinfo *)((char*)h+sizeof(*h));
        char index[IF_NAMESIZE];
        /* logdebug("mcast to local interface %d\n", i->ipi_ifindex); */
        if (if_indextoname(i->ipi_ifindex, index)) {
            strcpy(localip, inet_ntoa(i->ipi_spec_dst));
            /*
            logdebug("detail:%s %s %s\n", index, inet_ntoa(i->ipi_spec_dst),
                      inet_ntoa(i->ipi_addr));
            */
        }

        /* do nothing if they are same as we already have */
        if (g_c->clc_ip && strcmp(g_c->clc_ip, ip) == 0 &&
            g_c->clc_port == port ) {
            logdebug(_("same join message received\n"));
            return 0;
        }

        /* logging the result */
        logwarn(_("New clc host info received(%s %d %s)\n"), ip, port, localip);

        /* update clc info */
        if (g_c->clc_ip == NULL) {
            g_c->clc_ip = strdup(ip);
            g_c->clc_port = port;
            if (g_c->node_ip)
                free(g_c->node_ip);
            g_c->node_ip = strdup(localip);
            logwarn(_("New clc host info will be used\n"));
            return 1; /* (re)register is needed */
        }
        logwarn(_("New clc host info ignored\n"));
        return 0;
    }

    return -2; /* got data, but not useful */
}

/* curtosy of www.tenouk.com */
int ly_epoll_mcast_register()
{
    if (g_c == NULL || g_c->efd < 0 || g_c->mfd != -1)
        return -255;

    int ret = 0;
    NodeConfig *c = &g_c->config;

    /* Create a datagram socket on which to receive. */
    int sd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sd < 0) {
        logerror(_("Opening datagram socket error %s"), __func__);
        return -1;
    }

    /* Enable SO_REUSEADDR */
    int reuse = 1;
    if (setsockopt (sd, SOL_SOCKET, SO_REUSEADDR, (char *) &reuse, sizeof(reuse)) < 0) {
        logerror(_("Setting SO_REUSEADDR error %s"), __func__);
        close(sd);
        return -1;
    }

    /* Bind to the proper port number with the IP address specified as INADDR_ANY. */
    struct sockaddr_in localSock;
    memset((char *) &localSock, 0, sizeof(localSock));
    localSock.sin_family = AF_INET;
    localSock.sin_port = htons(c->clc_mcast_port);
    localSock.sin_addr.s_addr = INADDR_ANY;
    if (bind(sd, (struct sockaddr *) &localSock, sizeof(localSock))) {
        logerror(_("Binding datagram socket error %s"), __func__);
        close(sd);
        return -1;
    }

    /* make socket nonblocking */
    ret = lyutil_make_socket_nonblocking(sd); 
    if (ret != 0) {
        logerror(_("Making socket nonblocking error %s"), __func__);
        close(sd);
        return -1;
    }

    /* Join the multicast group on INADDR_ANY interface */
    /*
    struct ip_mreq group;
    group.imr_multiaddr.s_addr = inet_addr(c->clc_mcast_ip);
    group.imr_interface.s_addr = INADDR_ANY;
    if (setsockopt (sd, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char *) &group, sizeof(group)) < 0) {
        logerror(_("Adding multicast group error %s"), __func__);
        close(sd);
        return -1;
    }
    */
    /* go through all INET interface */
    struct ifaddrs *ifaddr, *ifa;
    if (getifaddrs(&ifaddr) == -1) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        close(sd);
        return -1;
    }
    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        char host[NI_MAXHOST];
        if (ifa->ifa_addr == NULL || ifa->ifa_addr->sa_family != AF_INET)
            continue;
        /* get ip */
        int s = getnameinfo(ifa->ifa_addr, sizeof(struct sockaddr_in),
                            host, NI_MAXHOST, NULL, 0, NI_NUMERICHOST);
        if (s != 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            close(sd);
            return -1;
        }
        logdebug(_("mcast listen on %s\n"), host);
        struct ip_mreq group;
        group.imr_multiaddr.s_addr = inet_addr(c->clc_mcast_ip);
        group.imr_interface.s_addr = inet_addr(host);
        if (setsockopt (sd, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char *) &group, sizeof(group)) < 0) {
            logerror(_("Adding multicast group error %s"), __func__);
            close(sd);
            return -1;
        }
        logdebug(_("mcast listen on %s registered\n"), host);
    }


    /* enable receiving control message */
    int yes = 1;
    if (setsockopt (sd, IPPROTO_IP, IP_PKTINFO, (char *) &yes, sizeof(yes)) < 0) {
        logerror(_("Adding IP_PKTINFO option error %s"), __func__);
        close(sd);
        return -1;
    }

    /* prepare packet receive structure */
    if (ly_packet_init(&g_c->mfd_pkt) < 0 ) {
        logerror(_("ly_packet_init error in  %s\n"), __func__);
        close(sd);
        return -1;
    }
    if (g_c->mfd_cmsg == NULL) {
        g_c->mfd_cmsg_size = sizeof(struct cmsghdr)+sizeof(struct in_pktinfo);
        g_c->mfd_cmsg = malloc(g_c->mfd_cmsg_size);
        if (g_c->mfd_cmsg == NULL) {
            logerror(_("no memory in %s\n"), __func__);
            ret = -1;
            goto out;
        }
    }

    /* register event */
    struct epoll_event ev;
    ev.events = EPOLLIN;
    ev.data.fd = sd;
    ret = epoll_ctl(g_c->efd, EPOLL_CTL_ADD, sd, &ev);
    if (ret < 0) {
        logerror(_("Registering mcast epoll error %s\n"), __func__);
        ret = -1;
        goto out;
    }
    loginfo(_("Registering mcast event done(%d).\n"), sd);

out:
    if (ret < 0){
        close(sd);
        ly_epoll_mcast_close();
    }
    else
        g_c->mfd = sd;
    return ret;
}

/* mcast socket down */
int ly_epoll_mcast_close(void)
{
    if (g_c == NULL)
        return -255;

    if (g_c->mfd >= 0)
        close(g_c->mfd);
    g_c->mfd = -1;
    
    ly_packet_cleanup(&g_c->mfd_pkt);

    if (g_c->mfd_cmsg != NULL) {
        free(g_c->mfd_cmsg);
        g_c->mfd_cmsg = NULL;
    }

    return 0;
}

/* work socket down */
int ly_epoll_work_close(void)
{
    if (g_c == NULL)
        return -255;

    if (g_c->wfd >= 0)
        close(g_c->wfd);
    g_c->wfd = -1;

    ly_packet_cleanup(&g_c->wfd_pkt);

    g_c->state = NODE_STATUS_UNKNOWN;
    return 0;
}

/* events processing initialization */
int ly_epoll_init(unsigned int max_events)
{
    if (g_c == NULL)
        return -255;

    if (g_c->efd >= 0)
        close(g_c->efd);

    g_c->efd = epoll_create(max_events);
    if (g_c->efd == -1){
        logerror(_("epoll_create failed in %s.\n"), __func__);
        return -1;
    }

    return 0;
}

/* stop and clean event processing */
int ly_epoll_close(void)
{
    if (g_c == NULL || g_c->efd < 0)
        return -255;

    ly_epoll_mcast_close();
    ly_epoll_work_close();

    close(g_c->efd);
    g_c->efd = -1;
    return 0;
}

