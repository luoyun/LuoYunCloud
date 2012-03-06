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
#include <pthread.h>

#include "../util/logging.h"
#include "domain.h"

static pthread_mutex_t virt_mutex = PTHREAD_MUTEX_INITIALIZER;
virConnectPtr g_conn = NULL; 

static inline void __this_lock(void)
{
    pthread_mutex_lock(&virt_mutex);
}

static inline void __this_unlock(void)
{
    pthread_mutex_unlock(&virt_mutex);
}

static void __customErrorFunc(void *userdata, virErrorPtr err)
{
    if (err->code == VIR_ERR_NO_DOMAIN) {
        logdebug(_("domain not found\n"));
        return;
    }

    logprintf("Failure of libvirt library call:\n");
    logsimple("  Code: %d\n", err->code);
    logsimple("  Domain: %d\n", err->domain);
    logsimple("  Message: %s\n", err->message);
    logsimple("  Level: %d\n", err->level);
    logsimple("  str1: %s\n", err->str1);
    logsimple("  str2: %s\n", err->str2);
    logsimple("  str3: %s\n", err->str3);
    logsimple("  int1: %d\n", err->int1);
    logsimple("  int2: %d\n", err->int2);
}

int libvirt_connect(int driver)
{
    if (g_conn != NULL) {
        logwarn(_("conneted already.\n"));
        return -1;
    }

    virSetErrorFunc(NULL, __customErrorFunc);

    const char * URI;
    if (driver == HYPERVISOR_IS_KVM)
        URI = HYPERVISOR_URI_KVM;
    else if (driver == HYPERVISOR_IS_XEN)
        URI = HYPERVISOR_URI_XEN;
    else {
        logerror(_("unrecognized hypervisor driver(%d).\n"), driver);
        return -1;
    }

    __this_lock();
    g_conn = virConnectOpen(URI);
    __this_unlock();
    if (g_conn == NULL) {
        logerror(_("Connet to %s error.\n"), URI);
        return -1;
    } 
    else {
        loginfo(_("Connect to %s success!\n"), URI);
    }

    return 0;
}

void libvirt_close(void)
{
    if (g_conn == NULL)
        return;

    virConnectClose(g_conn);
    __this_lock();
    g_conn = NULL;
    __this_unlock();
    return;
}

int libvirt_hypervisor(void)
{
    if (g_conn == NULL)
        return -1;

    const char *type;
    type = virConnectGetType(g_conn);
    if (NULL == type) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    if (!strcasecmp("QEMU", type))
        return HYPERVISOR_IS_KVM;
    else if (!strcasecmp("XEN", type))
        return HYPERVISOR_IS_XEN;
    else
        return HYPERVISOR_IS_UNKNOWN;

    /* no need to free */
    /* free(type); */
}

char * libvirt_hostname(void)
{
    if (g_conn == NULL)
        return NULL;

    char * n = virConnectGetHostname(g_conn);
    if (n)
        return strdup(n);
    else {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return NULL;
    }
}

int libvirt_max_cpus(void)
{
    if (g_conn == NULL)
        return -1;

    int max_cpus = virConnectGetMaxVcpus(g_conn, NULL);
    if (max_cpus < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    return max_cpus;
}

int libvirt_node_info(NodeInfo * ni)
{
    if (g_conn == NULL)
        return -1;

    virNodeInfo *nf;
    nf = malloc(sizeof(virNodeInfo));
    if (nf == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    /* success = 0, failed = -1 */
    if (virNodeGetInfo(g_conn, nf) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }

    __this_lock();
    ni->cpu_model = strdup(nf->model);
    ni->max_memory = nf->memory;
    ni->max_cpus = nf->cpus;
    ni->cpu_mhz = nf->mhz;
    /*
    ni->numaNodes = nf->nodes;
    ni->sockets = nf->sockets;
    ni->coresPerSocket = nf->cores;
    ni->threadsPerCore = nf->threads;
    */
    __this_unlock();

    free(nf);
    return 0;
}

unsigned int libvirt_free_memory(void)
{
    if (g_conn == NULL)
        return 0;

    /* can also use virNodeGetMemoryStats */
    int free_memory = virNodeGetFreeMemory(g_conn);
    if (free_memory == 0)
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
    return free_memory;
}

int libvirt_domain_active(char * name)
{
    if (g_conn == NULL)
        return 0;

    virDomainPtr domain = virDomainLookupByName(g_conn, name);
    int active = domain ? 1 : 0;
    if (domain)
        virDomainFree(domain);

    return active;
}

virDomainPtr libvirt_domain_create(char * xml)
{
    if (g_conn == NULL)
        return NULL;

    virDomainPtr domain = virDomainCreateXML(g_conn, xml, 0);
    if (domain == NULL) {
        logerror(_("%s: creating domain error\n"), __func__);
    }

    return domain;
}

int libvirt_domain_stop(char * name)
{
    if (g_conn == NULL)
        return -1;

    virDomainPtr domain;
    domain = virDomainLookupByName(g_conn, name);
    if (domain == NULL) {
        logerror(_("%s: connect domain by name(%s) error.\n"),
                   __func__, name);
        return -1;
    }

    if (virDomainShutdown(domain) != 0) {
        logerror(_("%s: shutdown domain error.\n"), __func__);
        virDomainFree(domain);
        return -1;
    }

    virDomainFree(domain);
    return 0;
}

int libvirt_domain_reboot(char * name)
{
    virDomainPtr domain;
    domain = virDomainLookupByName(g_conn, name);
    if (domain == NULL) {
        logerror(_("%s: connect domain by name(%s) error.\n"),
                   __func__, name);
        return -1;
    }

    if (virDomainReboot(domain, 0) != 0) {
        logerror(_("%s: reboot domain error.\n"), __func__);
        virDomainFree(domain);
        return -1;
    }

    return 0;
}

#if 0
int libvirt_domain_save(char * name, int idonweb)
{
    virDomainPtr domain;
    domain = virDomainLookupByName(g_conn, name);
    if (domain == NULL) {
        logerror(_("%s: connect domain by name(%s) error.\n"),
                   __func__, name);
        return -1;
    }

    virDomainInfo info;

    if (virDomainGetInfo(dom, &info) < 0) {
        logprintfl(SCERROR, "Cannot check guest state\n");
        return -3;
    }

    if (info.state == VIR_DOMAIN_SHUTOFF) {
        logprintfl(SCERROR, "Not saving guest that isn't running\n");
        return -4;
    }
    const char *filename = "";
    if (virDomainSave(dom, filename) < 0) {
        fprintf(stderr, "Unable to save guest to %s\n", filename);
    }

    fprintf(stdout, "Guest state saved to %s\n", filename);

    virConnectClose(conn);
    return 0;

}

#endif
