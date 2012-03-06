#ifndef __LUOYUN_INCLUDE_util_lyxml_H
#define __LUOYUN_INCLUDE_util_lyxml_H

#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/encoding.h>
#include <libxml/xmlwriter.h>
#include <libxml/xpath.h>
#include <libxml/xpathInternals.h>

#include "../luoyun/luoyun.h"

#ifndef LIBXML_TREE_ENABLED
#error "tree support not compiled in."
#endif
#if !defined(LIBXML_WRITER_ENABLED) || !defined(LIBXML_OUTPUT_ENABLED)
#error "xml writer not compiled in."
#endif

#define LYXML_ENCODING "ISO-8859-1"
#define LYXML_VERSION "1.0"
#define LYXML_ROOT "luoyun"

int lyclc_new_request_id(void);
int lynode_new_request_id(void);

/*
** helper functions based on libxml2
*/
void print_xml_element(xmlNode * cur_node);
void print_xml_doc(xmlDocPtr doc);
xmlDoc *xml_doc_from_str(const char *xmlstr);
int xml_xpath_exist_from_ctx(xmlXPathContextPtr xpathCtx,
                             const char * xpathExpr);
char *xml_xpath_text_from_ctx(xmlXPathContextPtr xpathCtx,
                              const char * xpathExpr);
char *xml_xpath_prop_from_ctx(xmlXPathContextPtr xpathCtx,
                              const char * xpathExpr, const char * prop);
char *xml_xpath_text_from_str(const char * xml, const char * xpathExpr);
char *xml_xpath_prop_from_str(const char * xml, const char * xpathExpr,
                              const char * prop);
void lyxml_doc_cleanup(xmlDoc * doc);
int lyxml_init(void);
void lyxml_cleanup(void);
int lyxml_process(char * xml, int (* req_func)(), int (* resp_func)(), int data);

/*
** building xml packet data
*/
char * lyxml_data_join(int id, char * host, int port,
                       char * buf, unsigned int size);
char * lyxml_data_node_register(NodeInfo * ni, char * buf, unsigned int size);
char * lyxml_data_node_info(int req_id, char * buf, unsigned int size);
char * lyxml_data_reply_auth_info(LYReply * reply, char * buf, unsigned int size);
char * lyxml_data_instance_run(NodeCtrlInstance * ci, char * buf, unsigned int size);
char * lyxml_data_instance_stop(NodeCtrlInstance * ci, char * buf, unsigned int size);
char * lyxml_data_instance_other(NodeCtrlInstance * ci, char * buf, unsigned int size);
char * lyxml_data_instance_register(int id, char * hostname, char * ip,
                                    char * buf, unsigned int size);
char * lyxml_data_reply(LYReply * reply, char * buf, unsigned int size);
char * lyxml_data_reply_instance_info(LYReply * reply, char * buf, unsigned int size);
char * lyxml_data_reply_node_info(LYReply * reply, char * buf, unsigned int size);
char * lyxml_data_report(LYReport * r, char * buf, unsigned int size);

#endif
