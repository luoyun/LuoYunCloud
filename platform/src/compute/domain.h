#ifndef  __LY_INCLUDE_COMPUTE_DOMAIN_H
#define  __LY_INCLUDE_COMPUTE_DOMAIN_H

#include <libvirt/libvirt.h>
#include <libvirt/virterror.h>
#include "lynode.h"

#define HYPERVISOR_URI_KVM "qemu:///system"
#define HYPERVISOR_URI_XEN "xen:///"

int libvirt_check(int driver);
int libvirt_connect(int driver);
void libvirt_close(void);
int libvirt_hypervisor(void);
char * libvirt_hostname(void);
int libvirt_max_cpus(void);
int libvirt_node_info(NodeInfo * ni);
int libvirt_node_info_update(NodeInfo * ni);
unsigned int libvirt_free_memory(void);
int libvirt_domain_active(char * name);
int libvirt_domain_create(char * xml);
int libvirt_domain_stop(char * name);
int libvirt_domain_poweroff(char * name);
int libvirt_domain_reboot(char * name);
char * libvirt_domain_xml(char * name);
int libvirt_domain_ifstat(char * name, char * target,
                          unsigned long * rx_bytes,
                          unsigned long * rx_pkts,
                          unsigned long * tx_bytes,
                          unsigned long * tx_pkts);


#if 0
int libvirt_domain_save(char * name, int idonweb)
#endif

#endif
