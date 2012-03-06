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
#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/encoding.h>
#include <libxml/xmlwriter.h>

#ifndef LIBXML_TREE_ENABLED
#error "tree support not compiled in."
#endif
#if !defined(LIBXML_WRITER_ENABLED) || !defined(LIBXML_OUTPUT_ENABLED)
#error "xml writer not compiled in."
#endif

#define LYXML_ENCODING "ISO-8859-1"
#define LYXML_VERSION "1.0"
#define LYXML_ROOT "luoyun"

typedef struct NodeInfo_t {
    int64_t max_memory;
    int64_t free_memory;
    int16_t max_cpus;
    int16_t cpu_mhz;
    int16_t load_average;
    int16_t port;
    int8_t active_flag;
    int8_t status;
    int8_t arch;                /* cpu arch */
    int8_t hypervisor;
    int8_t network_type;
    char cpu_model[32];
    char hostname[32];
    char ip[32];                /* eg 192.168.0.1 */
} NodeInfo;

NodeInfo nf = {
    .status = 0,
    .hostname = "localhost",
    .ip = "",
    .port = 0,
    .arch = 0,
    .hypervisor = 1,
    .network_type = 0,
    .max_memory = 602112,
    .max_cpus = 1,
    .cpu_model = "x86_64",
    .cpu_mhz = 2387,
    .load_average = 0,
    .free_memory = 459550720,
};

#if 0
/* 
** build and return < ... >, upon successful return
** *size contains the string length.
**
** The returned string needs to be freed with xmlfree()
*/
char *lycmd_xml_template(int *size)
{
    xmlNodePtr n;
    xmlNodePtr node;
    xmlDocPtr doc;

    doc = xmlNewDoc(BAD_CAST LYXML_VERSION);
    n = xmlNewNode(NULL, BAD_CAST LYXML_ROOT);
    xmlDocSetRootElement(doc, n);

    node = xmlNewChild(n, NULL, BAD_CAST "from", NULL);
    xmlNewProp(node, BAD_CAST "entity", BAD_CAST "???");

    node = xmlNewChild(n, NULL, BAD_CAST "to", NULL);
    xmlNewProp(node, BAD_CAST "entity", BAD_CAST "???");

    xmlChar *xmlbuff = NULL;
    int buffersize;
    xmlDocDumpFormatMemory(doc, &xmlbuff, &buffersize, 0);
    *size = buffersize;

    xmlFreeDoc(doc);
    return ((char *) xmlbuff);
}

/* line# 106
**
** use xmlTextWriterStartDocument() method to build and return
** < ... >, upon successful return (*size) contains the
** string length.
**
** The returned string needs to be freed with free()
*/
char *lycmd_xml_template(<... >, int *size)
{
    int ret = -1, rc;
    xmlBufferPtr buf;
    xmlTextWriterPtr writer;

    buf = xmlBufferCreate();
    if (buf == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        return NULL;
    }

    writer = xmlNewTextWriterMemory(buf, 0);
    if (writer == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        xmlBufferFree(buf);
        return NULL;
    }

    rc = xmlTextWriterStartDocument(writer, LYXML_VERSION, LYXML_ENCODING,
                                    NULL);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun */
    rc = xmlTextWriterStartElement(writer, BAD_CAST LYXML_ROOT);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/from */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "from");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "node")
        || xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/to */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "to");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "clc")
        || xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "request");
    if (rc < 0 ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "id",
                                          "%d", lynode_new_request_id())) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "action");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "name",
                                    BAD_CAST "register")
        || xmlTextWriterWriteAttribute(writer, BAD_CAST "reply",
                                       BAD_CAST "yes")) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action/parameters */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "parameters");
    if (rc < 0 || <... > xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* no need to close other elements since this is the end of the xml stream */
    ret = 0;

  out:
    rc = xmlTextWriterEndDocument(writer);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        ret = -1;
    }
    xmlFreeTextWriter(writer);
    if (ret < 0) {
        xmlBufferFree(buf);
        return NULL;
    }
    else {
        char *str = strdup((const char *) buf->content);
        *size = strlen(str);
        xmlBufferFree(buf);
        return str;
    }
}

#endif

int lyclc_new_request_id(void)
{
    static unsigned int id = 1;
    return id++;
}

int lynode_new_request_id(void)
{
    static unsigned int id = 1;
    return id++;
}

void print_element_names(xmlNode * cur_node)
{
    for (; cur_node; cur_node = cur_node->next) {
        if (cur_node->type == XML_ELEMENT_NODE) {
            printf("node type: Element, name: %s\n", cur_node->name);
            xmlAttrPtr attr = cur_node->properties;
            for (; attr; attr = attr->next)
                printf("\tAttribute %s = %s\n", attr->name,
                       xmlGetProp(cur_node, attr->name));
        }
        if (cur_node->type == XML_TEXT_NODE) {
            printf("node type: TEXT, name: %s\n", cur_node->content);
        }
        print_element_names(cur_node->children);
    }
    return;
}

void print_xml_doc(xmlDocPtr doc)
{
    xmlNode *root_element = xmlDocGetRootElement(doc);
    print_element_names(root_element);
}

xmlDoc *xml_doc_from_str(const char *xmlstr)
{
    return xmlReadDoc((xmlChar *) xmlstr, NULL, NULL, 0);
}

void xml_cleanup(xmlDoc * doc)
{
    xmlFreeDoc(doc);
    return;
}

#if 0
/* 
**
** use xmlNewNode() method to build and return clc mcast join
** command, upon successful return (*size) contains the string length.
**
** The returned string needs to be freed with xmlfree()
*/
char *lycmd_xml_clc_mcast_join(int *size)
{
    xmlNodePtr n;
    xmlNodePtr node;
    xmlDocPtr doc;

    doc = xmlNewDoc(BAD_CAST LYXML_VERSION);
    n = xmlNewNode(NULL, BAD_CAST LYXML_ROOT);
    xmlDocSetRootElement(doc, n);

    node = xmlNewChild(n, NULL, BAD_CAST "from", NULL);
    xmlNewProp(node, BAD_CAST "entity", BAD_CAST "clc");

    node = xmlNewChild(n, NULL, BAD_CAST "to", NULL);
    xmlNewProp(node, BAD_CAST "entity", BAD_CAST "node");

    node = xmlNewChild(n, NULL, BAD_CAST "request", NULL);
    xmlNewProp(node, BAD_CAST "id", BAD_CAST "1");

    node = xmlNewChild(node, NULL, BAD_CAST "action", NULL);
    xmlNewProp(node, BAD_CAST "name", BAD_CAST "join");
    xmlNewProp(node, BAD_CAST "reply", BAD_CAST "no");

    node = xmlNewChild(node, NULL, BAD_CAST "parameters", NULL);

    xmlNodePtr node1;
    node1 = xmlNewChild(node, NULL, BAD_CAST "host", NULL);
    xmlNewProp(node1, BAD_CAST "ip", BAD_CAST "192.168.1.107");
    node1 = xmlNewChild(node, NULL, BAD_CAST "port", NULL);
    xmlNewProp(node1, BAD_CAST "port", BAD_CAST "1450");

    xmlChar *xmlbuff = NULL;
    int buffersize;
    xmlDocDumpFormatMemory(doc, &xmlbuff, &buffersize, 0);
    *size = buffersize;

    xmlFreeDoc(doc);
    return ((char *) xmlbuff);
}

#else

/* 
**
** use xmlTextWriterStartDocument() method to build and return clc 
** mcast join command, upon successful return (*size) contains the
** string length.
**
** The returned string needs to be freed with free()
*/
char *lycmd_xml_clc_mcast_join(int *size)
{
    int ret = -1, rc, rc1, rc2;
    xmlBufferPtr buf;
    xmlTextWriterPtr writer;

    buf = xmlBufferCreate();
    if (buf == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        return NULL;
    }

    writer = xmlNewTextWriterMemory(buf, 0);
    if (writer == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        xmlBufferFree(buf);
        return NULL;
    }

    rc = xmlTextWriterStartDocument(writer, LYXML_VERSION, LYXML_ENCODING,
                                    NULL);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun */
    rc = xmlTextWriterStartElement(writer, BAD_CAST LYXML_ROOT);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/from */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "from");
    rc1 =
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "clc");
    rc2 = xmlTextWriterEndElement(writer);
    if (rc < 0 || rc1 < 0 || rc2 < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/to */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "to");
    rc1 =
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "node");
    rc2 = xmlTextWriterEndElement(writer);
    if (rc < 0 || rc1 < 0 || rc2 < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "request");
    rc1 = xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "id",
                                            "%d", lyclc_new_request_id());
    if (rc < 0 || rc1 < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "action");
    rc1 =
        xmlTextWriterWriteAttribute(writer, BAD_CAST "name",
                                    BAD_CAST "join");
    rc2 =
        xmlTextWriterWriteAttribute(writer, BAD_CAST "reply",
                                    BAD_CAST "no");
    if (rc < 0 || rc1 < 0 || rc2 < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action/parameters */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "parameters");
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action/parameters/host */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "host");
    rc1 =
        xmlTextWriterWriteAttribute(writer, BAD_CAST "ip",
                                    BAD_CAST "192.168.1.107");
    rc2 = xmlTextWriterEndElement(writer);
    if (rc < 0 || rc1 < 0 || rc2 < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action/parameters/port */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "port");
    rc1 =
        xmlTextWriterWriteAttribute(writer, BAD_CAST "port",
                                    BAD_CAST "1450");
    rc2 = xmlTextWriterEndElement(writer);
    if (rc < 0 || rc1 < 0 || rc2 < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* no need to close other elements since this is the end of the xml stream */
    ret = 0;
  out:
    rc = xmlTextWriterEndDocument(writer);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        ret = -1;
    }
    xmlFreeTextWriter(writer);
    if (ret < 0) {
        xmlBufferFree(buf);
        return NULL;
    }
    else {
        char *str = strdup((const char *) buf->content);
        *size = strlen(str);
        xmlBufferFree(buf);
        return str;
    }
}
#endif

/* 
**
** use xmlTextWriterStartDocument() method to build and return node 
** register, upon successful return (*size) contains the
** string length.
**
** The returned string needs to be freed with free()
*/
char *lycmd_xml_node_register_request(NodeInfo * nf, int *size)
{
    int ret = -1, rc;
    xmlBufferPtr buf;
    xmlTextWriterPtr writer;

    buf = xmlBufferCreate();
    if (buf == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        return NULL;
    }

    writer = xmlNewTextWriterMemory(buf, 0);
    if (writer == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        xmlBufferFree(buf);
        return NULL;
    }

    rc = xmlTextWriterStartDocument(writer, LYXML_VERSION, LYXML_ENCODING,
                                    NULL);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun */
    rc = xmlTextWriterStartElement(writer, BAD_CAST LYXML_ROOT);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/from */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "from");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "node")
        || xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/to */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "to");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "clc")
        || xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "request");
    if (rc < 0 ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "id",
                                          "%d", lynode_new_request_id())) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "action");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "name",
                                    BAD_CAST "register")
        || xmlTextWriterWriteAttribute(writer, BAD_CAST "reply",
                                       BAD_CAST "yes")) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/request/action/parameters */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "parameters");
    if (rc < 0 ||
        xmlTextWriterStartElement(writer, BAD_CAST "status") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "v",
                                          "%d", nf->status) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "host") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "name",
                                          "%s", nf->hostname) ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "ip",
                                          "%s", nf->ip) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "port") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "port",
                                          "%d", nf->port) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "arch") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "v",
                                          "%d", nf->arch) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "hypervisor") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "v",
                                          "%d", nf->hypervisor) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "network") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "type",
                                          "%d", nf->network_type) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "memory") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "total",
                                          "%ld", nf->max_memory) ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "free",
                                          "%ld", nf->free_memory) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "cpu") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "model",
                                          "%s", nf->cpu_model) ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "mhz",
                                          "%d", nf->cpu_mhz) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "vcpu") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "max",
                                          "%d", nf->max_cpus) ||
        xmlTextWriterEndElement(writer) ||
        xmlTextWriterStartElement(writer, BAD_CAST "load") ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "average",
                                          "%d", nf->load_average) ||
        xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* no need to close other elements since this is the end of the xml stream */
    ret = 0;

  out:
    rc = xmlTextWriterEndDocument(writer);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        ret = -1;
    }
    xmlFreeTextWriter(writer);
    if (ret < 0) {
        xmlBufferFree(buf);
        return NULL;
    }
    else {
        char *str = strdup((const char *) buf->content);
        *size = strlen(str);
        xmlBufferFree(buf);
        return str;
    }
}

/*
**
** use xmlTextWriterStartDocument() method to build and return clc response
** command, upon successful return (*size) contains the
** string length.
**
** The returned string needs to be freed with free()
*/
char *lycmd_xml_clc_response(int request_id, int ok, int *size)
{
    int ret = -1, rc;
    xmlBufferPtr buf;
    xmlTextWriterPtr writer;

    buf = xmlBufferCreate();
    if (buf == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        return NULL;
    }

    writer = xmlNewTextWriterMemory(buf, 0);
    if (writer == NULL) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        xmlBufferFree(buf);
        return NULL;
    }

    rc = xmlTextWriterStartDocument(writer, LYXML_VERSION, LYXML_ENCODING,
                                    NULL);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun */
    rc = xmlTextWriterStartElement(writer, BAD_CAST LYXML_ROOT);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/from */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "from");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "clc")
        || xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/to */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "to");
    if (rc < 0 ||
        xmlTextWriterWriteAttribute(writer, BAD_CAST "entity",
                                    BAD_CAST "node")
        || xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/response */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "response");
    if (rc < 0 ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "id",
                                          "%d", request_id)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* /luoyun/response/result */
    rc = xmlTextWriterStartElement(writer, BAD_CAST "result");
    if (rc < 0 ||
        xmlTextWriterWriteFormatAttribute(writer, BAD_CAST "v",
                                          "%d", ok) ||
        xmlTextWriterEndElement(writer)) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        goto out;
    }

    /* no need to close other elements since this is the end of the xml stream */
    ret = 0;

  out:
    rc = xmlTextWriterEndDocument(writer);
    if (rc < 0) {
        printf("Error in %s, line %d\n", __func__, __LINE__);
        ret = -1;
    }
    xmlFreeTextWriter(writer);
    if (ret < 0) {
        xmlBufferFree(buf);
        return NULL;
    }
    else {
        char *str = strdup((const char *) buf->content);
        *size = strlen(str);
        xmlBufferFree(buf);
        return str;
    }
}
void test_lycmd_xml_clc_mcast_join(void)
{
    int cmdsize = 0;
    char *cmd = lycmd_xml_clc_mcast_join(&cmdsize);
    printf("lycmd_xml_mcast_join returns %p:%d\n", cmd, cmdsize);
    xmlDoc *doc = xml_doc_from_str(cmd);
    if (doc == NULL) {
        printf("error: could not parse xml string.\n");
        return;
    }
    xmlFree(cmd);
    print_xml_doc(doc);

#if 0
    xmlSaveFormatFileEnc(argc > 1 ? argv[1] : "-", doc, "UTF-8", 1);    /* debugging dump */
#else
    xmlChar *xmlbuff;
    int buffersize;
    xmlDocDumpFormatMemory(doc, &xmlbuff, &buffersize, 1);
    printf((char *) xmlbuff);
    xmlFree(xmlbuff);
#endif

    xml_cleanup(doc);
    return;
}

void test_lycmd_xml_node_register_request(void)
{
    int cmdsize = 0;
    char *cmd = lycmd_xml_node_register_request(&nf, &cmdsize);
    printf("lycmd_xml_node_register_request returns %p:%d\n", cmd,
           cmdsize);
    xmlDoc *doc = xml_doc_from_str(cmd);
    if (doc == NULL) {
        printf("error: could not parse xml string.\n");
        return;
    }
    xmlFree(cmd);
    print_xml_doc(doc);

#if 0
    xmlSaveFormatFileEnc(argc > 1 ? argv[1] : "-", doc, "UTF-8", 1);    /* debugging dump */
#else
    xmlChar *xmlbuff;
    int buffersize;
    xmlDocDumpFormatMemory(doc, &xmlbuff, &buffersize, 1);
    printf((char *) xmlbuff);
    xmlFree(xmlbuff);
#endif

    xml_cleanup(doc);
    return;
}

void test_lycmd_xml_clc_response(void)
{
    int cmdsize = 0;
    char *cmd = lycmd_xml_clc_response(1, 1, &cmdsize);
    printf("lycmd_xml_clc_response returns %p:%d\n", cmd, cmdsize);
    xmlDoc *doc = xml_doc_from_str(cmd);
    if (doc == NULL) {
        printf("error: could not parse xml string.\n");
        return;
    }
    xmlFree(cmd);
    print_xml_doc(doc);

#if 0
    xmlSaveFormatFileEnc(argc > 1 ? argv[1] : "-", doc, "UTF-8", 1);    /* debugging dump */
#else
    xmlChar *xmlbuff;
    int buffersize;
    xmlDocDumpFormatMemory(doc, &xmlbuff, &buffersize, 1);
    printf((char *) xmlbuff);
    xmlFree(xmlbuff);
#endif

    xml_cleanup(doc);
    return;
}


int main(int argc, char **argv)
{
    /*
     * this initialize the library and check potential ABI mismatches
     * between the version it was compiled for and the actual shared
     * library used.
     */
    LIBXML_TEST_VERSION;

    test_lycmd_xml_clc_mcast_join();
    test_lycmd_xml_node_register_request();
    test_lycmd_xml_clc_response();

    xmlCleanupParser();
    return 0;
}
