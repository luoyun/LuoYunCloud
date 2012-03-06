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
#include "lyxml.h"

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

void print_xml_element(xmlNode * cur_node)
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
        print_xml_element(cur_node->children);
    }
    return;
}

void print_xml_doc(xmlDocPtr doc)
{
    xmlNode *root_element = xmlDocGetRootElement(doc);
    print_xml_element(root_element);
}

char *xml_xpath_text_from_ctx(xmlXPathContextPtr xpathCtx,
                              const char * xpathExpr)
{
    if (xpathCtx == NULL || xpathExpr == NULL)
        return NULL;

    xmlXPathObjectPtr xpathObj =
        xmlXPathEvalExpression((const xmlChar *)xpathExpr, xpathCtx);
    if (xpathObj == NULL)
        return NULL;

    if (xpathObj->nodesetval == NULL ||
        xpathObj->nodesetval->nodeTab == NULL)
        return NULL;

    xmlNodePtr n = xpathObj->nodesetval->nodeTab[0]->children;
    if (xmlNodeIsText(n)) {
        char *ret = NULL;
        if (n->content) {
            ret = strdup((const char*)n->content);
        }
        xmlXPathFreeObject(xpathObj);
        return ret;
    }

    xmlXPathFreeObject(xpathObj);
    return NULL;
}

char *xml_xpath_prop_from_ctx(xmlXPathContextPtr xpathCtx,
                              const char * xpathExpr, const char * prop)
{
    if (xpathCtx == NULL || xpathExpr == NULL || prop == NULL)
        return NULL;

    xmlXPathObjectPtr xpathObj =
        xmlXPathEvalExpression((const xmlChar *)xpathExpr, xpathCtx);
    if (xpathObj == NULL ||
        xpathObj->nodesetval == NULL ||
        xpathObj->nodesetval->nodeTab == NULL)
        return NULL;

    char * str = (char *)xmlGetProp(xpathObj->nodesetval->nodeTab[0],
                                   (const xmlChar *)prop);

    xmlXPathFreeObject(xpathObj);
    return str;
}

char *xml_xpath_text_from_str(const char * xml, const char * xpathExpr)
{
    if (xml == NULL || xpathExpr == NULL)
        return NULL;

    xmlDoc * doc = xml_doc_from_str(xml);
    xmlXPathContextPtr xpathCtx = xmlXPathNewContext(doc);
    if(xpathCtx == NULL)
        return NULL;

    char * str = xml_xpath_text_from_ctx(xpathCtx, xpathExpr);

    xmlXPathFreeContext(xpathCtx);
    xmlFreeDoc(doc);
    return str;
}

char *xml_xpath_prop_from_str(const char * xml, const char * xpathExpr,
                              const char * prop)
{
    if (xml == NULL || xpathExpr == NULL || prop == NULL)
        return NULL;

    xmlDoc * doc = xml_doc_from_str(xml);
    xmlXPathContextPtr xpathCtx = xmlXPathNewContext(doc);
    if(xpathCtx == NULL)
        return NULL;

    xmlXPathObjectPtr xpathObj =
        xmlXPathEvalExpression((const xmlChar *)xpathExpr, xpathCtx);
    if (xpathObj == NULL ||
        xpathObj->nodesetval == NULL ||
        xpathObj->nodesetval->nodeTab == NULL)
        return NULL;

    char * str = (char *)xmlGetProp(xpathObj->nodesetval->nodeTab[0],
                                   (const xmlChar *)prop);

    xmlXPathFreeObject(xpathObj);
    xmlFreeDoc(doc);
    return str;
}

int xml_xpath_exist_from_ctx(xmlXPathContextPtr xpathCtx,
                             const char * xpathExpr)
{
    if (xpathCtx == NULL || xpathExpr == NULL)
        return 0;

    xmlXPathObjectPtr xpathObj =
        xmlXPathEvalExpression((const xmlChar *)xpathExpr, xpathCtx);
    if (xpathObj == NULL)
        return 0;

    xmlXPathFreeObject(xpathObj);
    return 1;
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

int lyxml_init(void)
{
    /* Init libxml */
    xmlInitParser();
    /*
     * this initialize the library and check potential ABI mismatches
     * between the version it was compiled for and the actual shared
     * library used.
     */
    LIBXML_TEST_VERSION;
    return 0;
}

void lyxml_cleanup(void)
{
    /* Shutdown libxml */
    xmlCleanupParser();
    return;
}

int lyxml_process(char * xml, int (* req_func)(), int (* resp_func)(), int data)
{
    int ret = 0;
    xmlDoc *doc = xml_doc_from_str(xml);
    if (doc == NULL) {
        /* error: could not parse xml string */
        return -1;
    }
    xmlNode * node = xmlDocGetRootElement(doc);
    if (node == NULL || strcmp((char *)node->name, LYXML_ROOT) != 0) {
        /* error: xml string not for "LYXML_ROOT" */
        return -1;
    }
    node = node->children;

    for (; node; node = node->next) {
        if (node->type == XML_ELEMENT_NODE) {
            if (strcmp((char *)node->name, "response") == 0 ) {
                ret = resp_func(doc, node, data);
                if (ret  < 0)
                    break;
            }
            else if (strcmp((char *)node->name, "request") == 0 ) {
                ret = req_func(doc, node, data);
                if (ret  < 0)
                    break;
            }
            /* other nodes ignored */
        }
    }
    xmlFreeDoc(doc);
    return ret;
}


