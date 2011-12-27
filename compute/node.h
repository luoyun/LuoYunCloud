#ifndef __LUOYUN_COMPUTE_node_INCLUDE_H
#define __LUOYUN_COMPUTE_node_INCLUDE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "util/misc.h"
#include "util/luoyun.h"
#include "compute/domain.h"


int init_node_info (CpConfig *c);
int node_dynamic_status (LyComputeServerConfig *sc);
void print_node_info (ComputeNodeInfo *N);

#if 0
virConnectPtr open_connect(char *type);
Node *open_node();
int empty_node(Node *node);
int init_node(Node *node);
int close_node(Node *node);
int print_node_info(Node *node);
#endif

/* dynamic attribute of node */
// ng = node get
//unsigned long long ng_free_memory(Node *node);

#endif /* End __LUOYUN_COMPUTE_node_INCLUDE_H */
