#ifndef INCLUDE_NODE_DOMAIN_H
#define INCLUDE_NODE_DOMAIN_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libvirt/libvirt.h>
#include <libvirt/virterror.h>

#include "util/misc.h"
#include "util/luoyun.h"
#include "compute/lynode.h"
#include "compute/options.h"


virConnectPtr libvirtd_connect(CpConfig *c);

int set_hypervisor (CpConfig *c);
int set_hostname (CpConfig *c);
int set_max_cpus (CpConfig *c);
int set_node_mixture (CpConfig *c);
int set_free_memory (CpConfig *c);

#if 0
/* 下列三个函数最好返回 DomainPtr */
virDomainPtr connect_domain_by_id(Node *node, int id);
virDomainPtr connect_domain_by_name(Node *node, char *name);
virDomainPtr connect_domain_by_UUID(Node *node, char *UUID);



int *id_list_of_active_domains(Node *node, int *num);
char **name_list_of_inactive_domains(Node *node, int *num);
int list_domains(NodePtr node);
char **list_domain_names(NodePtr node);

const char *domain_state_by_name(NodePtr node, char *name);


int vir_domain_control_shutdown(NodePtr node, char *name);
int vir_domain_control_reboot(NodePtr node, char *name);
int vir_domain_control_start(NodePtr node, char *name);
#endif

virDomainPtr domain_connect (virConnectPtr conn, char *name);
virDomainPtr create_transient_domain( virConnectPtr conn,
                                      char *xml );
int domain_stop (virConnectPtr conn, char *name);

#endif /* end INCLUDE_NODE_DOMAIN_H */
