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
#include <unistd.h>

#include "luoyun.h"
#include "logging.h"
#include "lynode.h"
#include "options.h"
#include "events.h"
#include "domain.h"
#include "node.h"
#include "misc.h"

static const char *g_kvmvmname = "dongwu";
static const char *g_kvmxml = "";

static const char *g_xenvmname = "test";
static const char *g_xenxml = "\
<domain type='xen' id='18'>\
    <name>test</name>\
    <os>\
    <type>linux</type>\
        <kernel>/home/dongwu/luoyun/luoyun-cloud/test/vmfiles/kernel</kernel>\
        <initrd>/home/dongwu/luoyun/luoyun-cloud/test/vmfiles/ramdisk</initrd>\
        <root>/dev/sda1</root>\
        <cmdline> ro</cmdline>\
    </os>\
    <memory>256000</memory>\
    <vcpu>1</vcpu>\
    <devices>\
        <disk type='file'>\
            <source file='/home/dongwu/luoyun/luoyun-cloud/test/vmfiles/root'/>\
            <target dev='sda1'/>\
        </disk>\
        <interface type='bridge'>\
            <source bridge='br0'/>\
            <mac address='aa:bb:cc:dd:ee:ff'/>\
            <script path='/etc/xen/scripts/vif-bridge'/>\
        </interface>\
    </devices>\
    <serial type='pty'>\
      <target port='0'/>\
    </serial>\
    <console type='pty'>\
      <target port='0'/>\
    </console>\
</domain>\
";


/* Global value */
NodeControl *g_c = NULL;

static int __print_config(NodeConfig * c)
{
    logdebug("NodeControl :\n"
             "  clc_ip = %s\n" "  clc_port = %d\n"
             "  clc_mcast_ip = %s\n" "  clc_mcast_port = %d\n"
             "  auto_connect = %d\n"
             "  node_data_dir = %s\n"
             "  conf_path = %s\n"
             "  sysconf_path = %s\n"
             "  log_path = %s\n"
             "  verbose = %d\n" "  debug = %d\n" "  daemon = %d\n",
             c->clc_ip, c->clc_port,
             c->clc_mcast_ip, c->clc_mcast_port,
             c->auto_connect,
             c->node_data_dir, c->conf_path, c->sysconf_path, c->log_path,
             c->verbose, c->debug, c->daemon);

    return 0;
}

static void __main_clean(int keeppid)
{
    if (g_c == NULL)
        return;

    NodeConfig *c = &g_c->config;

    libvirt_close();
    if (c->conf_path)
        free(c->conf_path);
    if (c->sysconf_path)
        free(c->sysconf_path);
    if (c->node_data_dir)
        free(c->node_data_dir);
    if (c->log_path)
        free(c->log_path);
    if (g_c->node)
        free(g_c->node);
    free(g_c);
    return;
}

static char * __build_xen_xml_from_template()
{
    char * tmpl = file2str("./vmfiles/txen.xml");
    if (tmpl == NULL) {
        logerror("file2str failed\n");
        return NULL;
    }
    char * xml = malloc(strlen(tmpl) + 1024);
    if (xml == NULL) {
        logerror("malloc failed\n");
        return NULL;
    }
#define LUOYUN_INSTANCE_DISK_FILE "/home/dongwu/luoyun/luoyun-cloud/test/vmfiles/os.img"
#define LUOYUN_INSTANCE_KERNEL_FILE "/home/dongwu/luoyun/luoyun-cloud/test/vmfiles/kernel"
#define LUOYUN_INSTANCE_INITRD_FILE "/home/dongwu/luoyun/luoyun-cloud/test/vmfiles/initrd"
    sprintf(xml, tmpl,
                 "12", g_xenvmname,
                 LUOYUN_INSTANCE_KERNEL_FILE,
                 LUOYUN_INSTANCE_INITRD_FILE,
                 "256000", "1",
                 LUOYUN_INSTANCE_DISK_FILE,
                 "aa:bb:cc:dd:ee:ff");
    free(tmpl);
    return xml;
}

static char * __build_kvm_xml_from_template()
{
    char * tmpl = file2str("./vmfiles/tkvm.xml");
    if (tmpl == NULL) {
        logerror("file2str failed\n");
        return NULL;
    }
    char * xml = malloc(strlen(tmpl) + 1024);
    if (xml == NULL) {
        logerror("malloc failed\n");
        return NULL;
    }
#define LUOYUN_INSTANCE_KVM_DISK_FILE "/home/dongwu/luoyun-cloud/test/vmfiles/os.img"
    sprintf(xml, tmpl,
                 "12", g_kvmvmname, 
                 "512000", "1",
                 LUOYUN_INSTANCE_KVM_DISK_FILE,
                 "aa:bb:cc:dd:ee:ff");
    free(tmpl);
    return xml;
}


int main(int argc, char *argv[])
{
    int ret, keeppidfile = 1;

    /* start initializeing g_c */
    g_c = malloc(sizeof(NodeControl));
    if (g_c == NULL) {
        printf(_("malloc for g_c have a error.\n"));
        return -255;
    }
    g_c->node = NULL;
    g_c->efd = -1;
    g_c->mfd = -1;
    g_c->wfd = -1;
    NodeConfig *c = &g_c->config;
    NodeSysConfig *s = &g_c->config_sys;

    /* parse command line option and configuration file */
    ret = node_config(argc, argv, c, s);
    if (ret == NODE_CONFIG_RET_HELP)
        usage();
    else if (ret == NODE_CONFIG_RET_VER)
        printf(_("%s : Version %s\n"), PROGRAM_NAME, PROGRAM_VERSION);
    else if (ret == NODE_CONFIG_RET_ERR_CMD)
        printf(_
               ("command line parsing error, use -h option to display usage\n"));
    else if (ret == NODE_CONFIG_RET_ERR_NOCONF) {
        printf(_
               ("missing lynode config file, default build-in settings are used.\n"));
        ret = 0;
    }
    else if (ret == NODE_CONFIG_RET_ERR_CONF)
        printf(_("reading config file %s returned error\n"), c->conf_path);
    else if (ret == NODE_CONFIG_RET_ERR_UNKNOWN)
        printf(_("internal error\n"));

    /* exit if ret is not zero */
    if (ret != 0)
        goto out;

    /* for debuuging */
    __print_config(c);

    /* Connect to libvirt daemon */
    if (libvirt_connect(c->driver) < 0) {
        logsimple(_("error connecting hypervisor.\n"));
        ret = -255;
        goto out;
    }

    /* Init node info */
    g_c->node = ly_node_info_init();
    if (g_c->node == NULL) {
        logsimple(_("error initializing node info.\n"));
        ret = -255;
        goto out;
    }

    /* start dommain */
    const char *name;
    const char *xml;
    if (c->driver == HYPERVISOR_IS_KVM) {
        xml = g_kvmxml;
        xml = __build_kvm_xml_from_template();
        name = g_kvmvmname;
    }
    else if (c->driver == HYPERVISOR_IS_XEN) {
        xml = g_xenxml;
        xml = __build_xen_xml_from_template();
        printf(xml);
        name = g_xenvmname;
    }
    else {
        printf("unrecognized driver\n");
        ret = -255;
        goto out;
    }

    virDomainPtr domain = libvirt_domain_create((char *) xml);
    if (domain == NULL) {
        printf("libvirt_domain_create failed\n");
        ret = -1;
        goto out;
    }

    /* wait for a while */
    printf("domain created, let it run for a while...\n");
    sleep(100);

    /* shutdown the domain */
    if (libvirt_domain_stop((char *) name)) {
        logerror(_("Stop domain \"%s\"failed.\n"), name);
        return -1;
    }

  out:
    __main_clean(keeppidfile);
    return ret;
}
