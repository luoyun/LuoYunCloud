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
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/mount.h>
#include <errno.h>
#include <pthread.h>

#include "../luoyun/luoyun.h"
#include "../util/logging.h"
#include "../util/lypacket.h"
#include "../util/lyxml.h"
#include "../util/lyutil.h"
#include "../util/disk.h"
#include "../util/download.h"
#include "domain.h"
#include "node.h"
#include "handler.h"

#define LIBVIRT_XML_DATA_MAX 2048

static pthread_mutex_t handler_mutex = PTHREAD_MUTEX_INITIALIZER;
static int g_handler_thread_num = 0;

/* check whether the handler is busy */
int ly_handler_busy(void)
{
    return g_handler_thread_num > LY_NODE_THREAD_MAX ? 1 : 0;
}

/* update g_handler_thread_num */
static void __update_thread_num(int change)
{
   pthread_mutex_lock(&handler_mutex);
   g_handler_thread_num += change;
   pthread_mutex_unlock(&handler_mutex);
   return;
}

/* send respond to control server */
static int __send_response(int socket, NodeCtrlInstance * ci, int status)
{
    LYReply r;
    r.req_id = ci->req_id;
    r.from = LY_ENTITY_NODE;
    r.to = LY_ENTITY_CLC;
    r.status = status;
    if (status == LY_S_FINISHED_SUCCESS) 
        r.msg = "success";
    else if (status == LY_S_FINISHED_FAILURE)
        r.msg = "fail";
    else if (status == LY_S_RUNNING_DOWNLOADING_APP)
        r.msg = "downloading appliance";
    else if (status == LY_S_RUNNING_CHECKING_APP)
        r.msg = "checking applaince checksum";
    else if (status == LY_S_RUNNING_EXTRACTING_APP)
        r.msg = "extracting instance disk";
    else if (status == LY_S_RUNNING_MOUNTING_IMAGE)
        r.msg = "mounting instance disk";
    else if (status == LY_S_RUNNING_PREPARING_IMAGE)
        r.msg = "finalizing instance disk";
    else if (status == LY_S_RUNNING_UNMOUNTING_IMAGE)
        r.msg = "un-mounting instance disk";
    else if (status == LY_S_RUNNING_STARTING_INSTANCE)
        r.msg = "starting instance domain";
    else if (status == LY_S_RUNNING_WAITING)
        r.msg = "waiting for resouces";
    else if (status == LY_S_RUNNING_STOPPING)
        r.msg = "instance shutting down";
    else if (status == LY_S_RUNNING_STOPPED)
        r.msg = "instance stopped";
    else
        r.msg = NULL;

    logdebug(_("sending responses ..., %s\n"), r.msg);
    char * xml = lyxml_data_reply(&r, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    int ret = ly_packet_send(socket, PKT_TYPE_CLC_INSTANCE_CONTROL_REPLY,
                             xml, strlen(xml));
    free(xml);
    if (ret < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }

    return 0;
}

/* lock handling file accessing */
static int __file_lock_get(char * lock_dir, char * lock_ext)
{
    if (lock_dir == NULL)
        return -1;
    if (access(lock_dir,  R_OK | W_OK | X_OK) != 0) {
        logerror(_("error in %s(%d). errno:%d\n"),
                    __func__, __LINE__, errno);
        return -1;
    }
    char path[PATH_MAX];
    if (snprintf(path, PATH_MAX, "%s/.forlock", lock_dir) >= PATH_MAX)
        return -1;
    int fd = creat(path, S_IWUSR);
    if (fd < 0 ){
        logerror(_("error in %s(%d). errno:%d\n"),
                    __func__, __LINE__, errno);
        return -1;
    }
    close(fd);
    char link_path[PATH_MAX];
    if (snprintf(link_path, PATH_MAX, "%s/.forlock.%s",
                 lock_dir, lock_ext) >= PATH_MAX)
        return -1;
    int time_warn = 30; 
    int time_warn_cnt = 20; 
    while (link(path, link_path) < 0) {
        /* someone has the lock already */
        if (time_warn == 0) {
            logwarn(_("waited thread lock for 30 seconds."
                      "continue waiting...\n"));
            time_warn = 30;
            time_warn_cnt--;
        }
        sleep(1);
        time_warn--;
        if (time_warn_cnt <= 0) {
            logerror(_("error in %s(%d).\n"), __func__, __LINE__);
            return -1;
        }
    }
    return 0; /* lock granted */
}
        
static int __file_lock_put(char * lock_dir, char * lock_ext)
{
    if (lock_dir == NULL)
        return -1;
    if (access(lock_dir,  R_OK | W_OK | X_OK) != 0) {
        logerror(_("error in %s(%d). errno:%d\n"),
                    __func__, __LINE__, errno);
        return -1;
    }
    char link_path[PATH_MAX];
    if (snprintf(link_path, PATH_MAX, "%s/.forlock.%s",
                 lock_dir, lock_ext) >= PATH_MAX)
        return -1;
    if (unlink(link_path) < 0) {
        logerror(_("error in %s(%d). unlink %s errno:%d\n"),
                    __func__, __LINE__, link_path, errno);
        return -1;
    }
    return 0; /* lock released */
}

static int __domain_dir_clean(char * dir, int keepdir)
{
    if (dir == NULL)
        return -1;

    char * files[] = { LUOYUN_INSTANCE_DISK_FILE,
                       LUOYUN_INSTANCE_CONF_FILE,
                       LUOYUN_INSTANCE_STORAGE1_FILE,
                       "kernel",
                       "initrd",
                       NULL };
    int i = 0;
    while (files[i]) {
        char path[PATH_MAX];
        snprintf(path, PATH_MAX, "%s/%s", dir, files[i]);
        if (access(path, R_OK) == 0 && unlink(path) != 0) {
            logerror(_("removing %s failed, %s.\n"), path, strerror(errno));
            return -1;
        }
        i++;
    }

    if (keepdir)
        return 0;

    if (rmdir(dir) != 0) {
        logerror(_("error removing %s, %s\n"), dir, strerror(errno));
        /* return -1; don't treat this as fatal error */
    }

    return 0;
}

/* create fat16 FS of size 1MB and luoyun.ini fle */
static FILE * __create_luoyun_ini(char * ini_path)
{
    char sec_boot[] = {
        0xeb, 0x3c, 0x90, 0x6d, 0x6b, 0x64, 0x6f, 0x73, 0x66, 0x73, 0x00, 0x00, 0x02, 0x01, 0x01, 0x00,
        0x02, 0x00, 0x02, 0x00, 0x08, 0xf8, 0x08, 0x00, 0x20, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x29, 0xed, 0xee, 0x74, 0xf0, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x46, 0x41, 0x54, 0x31, 0x36, 0x20, 0x20, 0x20, 0x0e, 0x1f,
        0xbe, 0x5b, 0x7c, 0xac, 0x22, 0xc0, 0x74, 0x0b, 0x56, 0xb4, 0x0e, 0xbb, 0x07, 0x00, 0xcd, 0x10,
        0x5e, 0xeb, 0xf0, 0x32, 0xe4, 0xcd, 0x16, 0xcd, 0x19, 0xeb, 0xfe, 0x54, 0x68, 0x69, 0x73, 0x20,
        0x69, 0x73, 0x20, 0x6e, 0x6f, 0x74, 0x20, 0x61, 0x20, 0x62, 0x6f, 0x6f, 0x74, 0x61, 0x62, 0x6c,
        0x65, 0x20, 0x64, 0x69, 0x73, 0x6b, 0x2e, 0x20, 0x20, 0x50, 0x6c, 0x65, 0x61, 0x73, 0x65, 0x20,
        0x69, 0x6e, 0x73, 0x65, 0x72, 0x74, 0x20, 0x61, 0x20, 0x62, 0x6f, 0x6f, 0x74, 0x61, 0x62, 0x6c,
        0x65, 0x20, 0x66, 0x6c, 0x6f, 0x70, 0x70, 0x79, 0x20, 0x61, 0x6e, 0x64, 0x0d, 0x0a, 0x70, 0x72,
        0x65, 0x73, 0x73, 0x20, 0x61, 0x6e, 0x79, 0x20, 0x6b, 0x65, 0x79, 0x20, 0x74, 0x6f, 0x20, 0x74,
        0x72, 0x79, 0x20, 0x61, 0x67, 0x61, 0x69, 0x6e, 0x20, 0x2e, 0x2e, 0x2e, 0x20, 0x0d, 0x0a, 0x00 };
    int len_boot = sizeof(sec_boot);
    int off_boot = 0;
    char sec_boot_sign[] = { 0x55, 0xaa };
    int len_boot_sign = 2;
    int off_boot_sign = 510;
    char sec_fat[] = {
        0xf8, 0xff, 0xff, 0xff, 0x40, 0x00, 0x05, 0x60, 0x00, 0x07, 0x80, 0x00, 0x09, 0xf0, 0xff, 0x00 };
    int len_fat = sizeof(sec_fat);
    int off_fat1 = 0x200;
    int off_fat2 = 0x1200;
    char sec_root[] = {
        0x41, 0x6c, 0x00, 0x75, 0x00, 0x6f, 0x00, 0x79, 0x00, 0x75, 0x00, 0x0f, 0x00, 0xca, 0x6e, 0x00,
        0x2e, 0x00, 0x69, 0x00, 0x6e, 0x00, 0x69, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
        0x4c, 0x55, 0x4f, 0x59, 0x55, 0x4e, 0x20, 0x20, 0x49, 0x4e, 0x49, 0x20, 0x00, 0x00, 0xd1, 0xa1,
        0x02, 0x41, 0x02, 0x41, 0x00, 0x00, 0xd1, 0xa1, 0x02, 0x41, 0x03, 0x00 };
    int len_root = sizeof(sec_root);
    int off_root = 0x2200;
    /* int off_data_len = off_root + len_root; */
    int off_data = 0x6400;

    int fd = creat(ini_path, S_IRUSR|S_IWUSR);
    if (fd < 0) {
        logerror(_("error creating file %s, %s\n"), ini_path, strerror(errno));
        return NULL;
    }

    if (lseek(fd, off_boot, SEEK_SET) < 0 ||
        write(fd, sec_boot, len_boot) < 0 ||
        lseek(fd, off_boot_sign, SEEK_SET) < 0 ||
        write(fd, sec_boot_sign, len_boot_sign) < 0 ||
        lseek(fd, off_fat1, SEEK_SET) < 0 ||
        write(fd, sec_fat, len_fat) < 0 ||
        lseek(fd, off_fat2, SEEK_SET) < 0 ||
        write(fd, sec_fat, len_fat) < 0 ||
        lseek(fd, off_root, SEEK_SET) < 0 ||
        write(fd, sec_root, len_root) < 0 ||
        lseek(fd, off_data, SEEK_SET) < 0) {
        logerror(_("error writing file %s, %s\n"), ini_path, strerror(errno));
        goto out;
    }

    FILE * fp = fdopen(fd, "w");
    if (fp == NULL) {
        logerror(_("error opening file %s, %s\n"), LUOYUN_INSTANCE_CONF_FILE,
                                                   strerror(errno));
        goto out;
    }

    return fp;
out:
    close(fd);
    unlink(ini_path);
    return NULL;
}

/* close luoyun.ini fle */
static int __close_luoyun_ini(FILE * fp)
{
    int fd = fileno(fp);
    long off_data_len = 0x223c; /* off_root + len_root */
    long off_data = 0x6400;
    long len_data = ftell(fp);
    if (len_data < 0) {
        logerror(_("error getting file position, %s\n"), strerror(errno));
        goto out;
    }
    if (len_data >= 1048576) {
        logerror(_("error writing file, ini file is too big\n"));
        goto out;
    }
    len_data -= off_data;
    if (lseek(fd, off_data_len, SEEK_SET) < 0 ||
        write(fd, (unsigned long *)&len_data, 4) < 0) {
        logerror(_("error writing file, %s\n"), strerror(errno));
        goto out;
    }
    if (ftruncate(fd, 1048576)) {
        logerror(_("error truncate file, %s\n"), strerror(errno));
        goto out;
    }
    fclose(fp);
    return 0;
out:
    fclose(fp);
    return -1;
}

#include <json.h>
static int __domain_xml_json(NodeCtrlInstance * ci, int hypervisor, 
                             char * net, int net_size, 
                             char * disk, int disk_size)
{
    if (ci == NULL || ci->osm_json == NULL || net == NULL || disk == NULL || g_c == NULL)
        return -1;

    char path[1024], tmp[1024];
    json_settings settings;
    memset((void *)&settings, 0, sizeof(json_settings));
    char error[256];
    json_value * value = json_parse_ex(&settings, ci->osm_json, error);
    if (value == 0) {
        logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, error);
        return -1;
    }

    if (value->type != json_object) {
        logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "object");
        goto out;
    }

    for (int i = 0; i < value->u.object.length; i++) {
        if (strcmp(value->u.object.values[i].name, "network") == 0) {
            net[0] = '\0';
            json_value * net_array = value->u.object.values[i].value;
            if (net_array->type != json_array) {
                logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "network");
                goto out;
            }
            for (int j = 0; j < net_array->u.array.length; j++) {
                json_value * net_value = net_array->u.array.values[j];
                if (net_value->type != json_object) {
                    logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "net object");
                    goto out;
                }
                json_value * net_mac = NULL;
                json_value * net_type = NULL;
                for (int k = 0; k < net_value->u.object.length; k++) {
                    if (strcmp(net_value->u.object.values[k].name, "mac") == 0) {
                        net_mac = net_value->u.object.values[k].value;
                    }
                    else if (strcmp(net_value->u.object.values[k].name, "type") == 0) {
                        net_type = net_value->u.object.values[k].value;
                    }
                    if (net_mac && net_type)
                        break;
                }
                if (net_mac == NULL || net_mac->type != json_string) {
                    logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "net mac");
                    goto out;
                }
                char * mac = net_mac->u.string.ptr;
                char * type = g_c->config.net_primary;
                if (j > 0 && g_c->config.net_secondary)
                    type = g_c->config.net_secondary;
                if (net_type) {
                    if (net_type->type != json_string) {
                        logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "net type");
                        goto out;
                    }
                }
                if (type == NULL || strcmp(type, "default") == 0 || strncmp(type, "virbr", 5) == 0) {
                    if (g_c->config.vm_xml_net_nat)
                        snprintf(tmp, 1024, g_c->config.vm_xml_net_nat, mac);
                    else if (hypervisor == HYPERVISOR_IS_XEN)
                        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_XEN_NET_NAT, mac);
                    else if (hypervisor == HYPERVISOR_IS_KVM)
                        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_KVM_NET_NAT, mac);
                    else {
                        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                        goto out;
                    }
                }
                else {
                    if (g_c->config.vm_xml_net_br)
                        snprintf(tmp, 1024, g_c->config.vm_xml_net_br, type, mac);
                    else if (hypervisor == HYPERVISOR_IS_XEN)
                        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_XEN_NET_BRIDGE, type, mac);
                    else if (hypervisor == HYPERVISOR_IS_KVM)
                        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_KVM_NET_BRIDGE, type, mac);
                    else {
                        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                        goto out;
                    }
                }
                if (strlen(net) + strlen(tmp) >= net_size) {
                    logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                    goto out;
                }
                strcat(net, tmp);
            }
        }
        else if (strcmp(value->u.object.values[i].name, "storage") == 0) {
            int storage_size = -1;
            int disk_found = 0;
            json_value * disk_array = value->u.object.values[i].value;
            if (disk_array->type != json_array) {
                logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "storage");
                goto out;
            }
            for (int j = 0; j < disk_array->u.array.length; j++) {
                json_value * disk_value = disk_array->u.array.values[j];
                if (disk_value->type != json_object) {
                    logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "disk");
                    goto out;
                }
                for (int k = 0; k < disk_value->u.object.length; k++) {
                    if (strcmp(disk_value->u.object.values[k].name, "type") == 0) {
                        json_value * disk_type = disk_value->u.object.values[k].value;
                        if (disk_type->type != json_string) {
                            logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "disk type");
                            goto out;
                        }
                        if (strcmp(disk_type->u.string.ptr, "disk") == 0) {
                            if (disk_found) {
                                /* only support one disk for now */
                                logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "dup disk");
                                goto out;
                            }
                            disk_found = 1;
                        }
                        else
                            /* ignore other disk types */
                            break;
                    }
                    else if (strcmp(disk_value->u.object.values[k].name, "size") == 0) {
                        json_value * disk_size = disk_value->u.object.values[k].value;
                        if (disk_size->type != json_integer || disk_size->u.integer <= 0) {
                            logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "disk size");
                            goto out;
                        }
                        storage_size = disk_size->u.integer;
                    }
                }
                if (disk_found) {
                    if (storage_size <= 0) {
                        logerror(_("error parsing json in %s(%d), %s\n"), __func__, __LINE__, "no disk size");
                        goto out;
                    }
                    if (snprintf(path, 1024, "%s/%d/%s", g_c->config.ins_data_dir,
                                 ci->ins_id, LUOYUN_INSTANCE_STORAGE1_FILE) >= 1024) {
                        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                        goto out;
                    }

                    if (g_c->config.vm_xml_disk)
                        snprintf(tmp, 1024, g_c->config.vm_xml_disk, path);
                    else if (hypervisor == HYPERVISOR_IS_XEN)
                        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_XEN_DISK, path, LUOYUN_INSTANCE_XEN_DISK2_NAME);
                    else if (hypervisor == HYPERVISOR_IS_KVM)
                        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_KVM_DISK, path, LUOYUN_INSTANCE_KVM_DISK2_NAME);
                    else {
                        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                        goto out;
                    }
                    if (strlen(disk) + strlen(tmp) > disk_size) {
                        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                        goto out;
                    }
                    strcat(disk, tmp);

                    int need_truncate = 1;
                    if (access(path, F_OK) == 0) {
                        struct stat statbuf;
                        if (stat(path, &statbuf)) {
                            logerror(_("error in %s(%d), %s(%d).\n"), __func__, __LINE__,
                                                                      strerror(errno), errno);
                            goto out;
                        }
                        int size_g = (int)(statbuf.st_size>>30);
                        if (size_g == storage_size)
                            need_truncate = 0;
                    }
                    else {
                        int fh = creat(path, S_IRUSR|S_IWUSR);
                        if (fh < 0) {
                            logerror(_("error in %s(%d), %s(%d).\n"), __func__, __LINE__,
                                                                     strerror(errno), errno);
                            goto out;
                        }
                        close(fh);
                    }
                    if (need_truncate) {
                        if (truncate(path, (off_t)storage_size<<30)) {
                            logerror(_("error in %s(%d), %s(%d).\n"), __func__, __LINE__,
                                                                      strerror(errno), errno);
                            goto out;
                        }
                    }
                }
            }
            if (disk_found == 0) {
                /* delete disk */
                if (snprintf(path, 1024, "%s/%d/%s", g_c->config.ins_data_dir,
                             ci->ins_id, LUOYUN_INSTANCE_STORAGE1_FILE) >= 1024) {
                    logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                    goto out;
                }
                if (access(path, F_OK) == 0) {
                    if (unlink(path)) {
                        logerror(_("error in %s(%d), %s(%d).\n"), __func__, __LINE__,
                                                                  strerror(errno), errno);
                        goto out;
                    }
                }
            }
        }
    }

    json_value_free(value);
    return 0;

out:
    json_value_free(value);
    return -1;
}

static char * __domain_xml(NodeCtrlInstance * ci, int hypervisor, int fullvirt)
{
    if (ci == NULL || g_c == NULL)
        return NULL;

    char net[1024], disk[1024];
    char path[1024], conf_path[1024];
    int disk_len;

    /* os disk */
    if (snprintf(path, 1024, "%s/%d/%s", g_c->config.ins_data_dir,
                 ci->ins_id, LUOYUN_INSTANCE_DISK_FILE) >= 1024) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return NULL;
    }
    if (g_c->config.vm_xml_disk)
        snprintf(disk, 1024, g_c->config.vm_xml_disk, path);
    else if (hypervisor == HYPERVISOR_IS_XEN)
        snprintf(disk, 1024, LIBVIRT_XML_TMPL_XEN_DISK, path, LUOYUN_INSTANCE_XEN_DISK1_NAME);
    else if (hypervisor == HYPERVISOR_IS_KVM)
        snprintf(disk, 1024, LIBVIRT_XML_TMPL_KVM_DISK, path, LUOYUN_INSTANCE_KVM_DISK1_NAME);
    else {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return NULL;
    }
    disk_len = strlen(disk);

    /* config disk */
    if (snprintf(conf_path, 1024, "%s/%d/%s", g_c->config.ins_data_dir,
                 ci->ins_id, LUOYUN_INSTANCE_CONF_FILE) >= 1024) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return NULL;
    }
#if 0 /* use floppy disk instead */
    if (g_c->config.vm_xml_disk)
        snprintf(tmp, 1024, g_c->config.vm_xml_disk, conf_path);
    else if (hypervisor == HYPERVISOR_IS_XEN)
        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_XEN_DISK, conf_path, LUOYUN_INSTANCE_XEN_DISK2_NAME);
    else if (hypervisor == HYPERVISOR_IS_KVM)
        snprintf(tmp, 1024, LIBVIRT_XML_TMPL_KVM_DISK, conf_path, LUOYUN_INSTANCE_KVM_DISK2_NAME);
    else {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return NULL;
    }
    if (strlen(disk) + strlen(tmp) >= 1024) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return NULL;
    }
    strcat(disk, tmp);
#endif

    /* prepare space for the complete XML */
    int size = LIBVIRT_XML_DATA_MAX;
    char * buf = malloc(size);
    if (buf == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return NULL;
    }

    net[0] = '\0';
    if (ci->osm_json) {
        if (__domain_xml_json(ci, hypervisor, net, 1024, disk, 1024) != 0) {
             logerror(_("error in %s(%d).\n"), __func__, __LINE__);
             goto out;
        }
    }

    if (disk_len == strlen(disk)) {
        /* delete disk */
        if (snprintf(path, 1024, "%s/%d/%s", g_c->config.ins_data_dir,
                     ci->ins_id, LUOYUN_INSTANCE_STORAGE1_FILE) >= 1024) {
            logerror(_("error in %s(%d).\n"), __func__, __LINE__);
            goto out;
        }
        if (access(path, F_OK) == 0) {
            if (unlink(path)) {
                logerror(_("error in %s(%d), %s(%d).\n"), __func__, __LINE__,
                           strerror(errno), errno);
                goto out;
            }
        }
    }

    if (net[0] == '\0') {
        char * type = g_c->config.net_primary;
        if (type == NULL || strcmp(type, "default") == 0 || strncmp(type, "virbr", 5) == 0) {
            if (g_c->config.vm_xml_net_nat)
                snprintf(net, 1024, g_c->config.vm_xml_net_nat, ci->ins_mac);
            else if (hypervisor == HYPERVISOR_IS_XEN)
                snprintf(net, 1024, LIBVIRT_XML_TMPL_XEN_NET_NAT, ci->ins_mac);
            else if (hypervisor == HYPERVISOR_IS_KVM)
                snprintf(net, 1024, LIBVIRT_XML_TMPL_KVM_NET_NAT, ci->ins_mac);
            else {
                logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                goto out;
            }
        }
        else {
            if (g_c->config.vm_xml_net_br)
                snprintf(net, 1024, g_c->config.vm_xml_net_br, type, ci->ins_mac);
            else if (hypervisor == HYPERVISOR_IS_XEN)
                snprintf(net, 1024, LIBVIRT_XML_TMPL_XEN_NET_BRIDGE, type, ci->ins_mac);
            else if (hypervisor == HYPERVISOR_IS_KVM)
                snprintf(net, 1024, LIBVIRT_XML_TMPL_KVM_NET_BRIDGE, type, ci->ins_mac);
            else {
                logerror(_("error in %s(%d).\n"), __func__, __LINE__);
                goto out;
            }
        }

    }

    int len = -1;
    if (g_c->config.vm_xml) {
        char strid[20], strmem[20], strcpu[10];
        sprintf(strid, "%d", ci->ins_id);
        sprintf(strmem, "%d", ci->ins_mem);
        sprintf(strcpu, "%d", ci->ins_vcpu);
        len =  snprintf(buf, size, g_c->config.vm_xml,
                        strid, ci->ins_domain,
                        strmem, strcpu, conf_path, disk, net);
    }
    else if (hypervisor == HYPERVISOR_IS_KVM) {
        len = snprintf(buf, size, LIBVIRT_XML_TMPL_KVM,
                       ci->ins_id, ci->ins_domain,
                       ci->ins_mem, ci->ins_vcpu, conf_path, disk, net);
    }
    else if (hypervisor == HYPERVISOR_IS_XEN && fullvirt) {
        len = -2;
    }
    else if (hypervisor == HYPERVISOR_IS_XEN && fullvirt == 0) {
        snprintf(path, 1024, "%s/%d", g_c->config.ins_data_dir, ci->ins_id);
        len = snprintf(buf, size, LIBVIRT_XML_TMPL_XEN_PARA,
                       ci->ins_id, ci->ins_domain, path, path,
                       ci->ins_mem, ci->ins_vcpu, conf_path, disk, net);
    }
    logsimple("%d\n", len);
    if (len < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out;
    }
    else if (len >= size) {
        logerror(_("xml string is too large\n"));
        goto out;
    }
    logsimple("%s\n", buf);

    return buf;

out:
    free(buf);
    return NULL;
}

static int __domain_run_data_check(NodeCtrlInstance * ci)
{
    if (ci == NULL || g_c == NULL)
        return -255;

    if (ci->ins_vcpu == 0)
        ci->ins_vcpu = LUOYUN_INSTANCE_CPU_DEFAULT;
    if (ci->ins_mem == 0)
        ci->ins_mem = LUOYUN_INSTANCE_MEM_DEFAULT;
    if (ci->ins_mac == NULL && ci->osm_json == NULL)
        return -1;
    if (ci->app_id == 0 ||
        ci->app_name == NULL ||
        ci->app_checksum == NULL)
        return -1;
    if (ci->app_uri == NULL) {
        ci->app_uri = malloc(LUOYUN_APPLIANCE_URI_MAX);
        if (ci->app_uri == NULL)
            return -1;
        if (snprintf(ci->app_uri, LUOYUN_APPLIANCE_URI_MAX,
                     LUOYUN_APPLIANCE_URI_TEMPLATE,
                     g_c->clc_ip,
                     ci->app_checksum) >= LUOYUN_APPLIANCE_URI_MAX)
            return -1;
    }
    if (ci->osm_clcip == NULL)
        ci->osm_clcip = strdup(g_c->clc_ip);
    if (ci->osm_clcport == 0)
        ci->osm_clcport = g_c->clc_port;

    return 0;
}

static int __domain_run(NodeCtrlInstance * ci)
{
    if (__domain_run_data_check(ci) < 0) {
        logerror(_("instance control data check failed\n"));
        luoyun_node_ctrl_instance_print(ci);
        return -1;
    }
    if (g_c->config.debug)
        luoyun_node_ctrl_instance_print(ci);

    int ret = -1;
    char path[PATH_MAX];
    char tmpstr1024[1024];

    char ins_idstr[10];
    snprintf(ins_idstr, 10, "%d", ci->ins_id);

    logdebug(_("trying to gain access to instance files...\n"));
    __send_response(g_c->wfd, ci, LY_S_RUNNING_WAITING);
    if (__file_lock_get(g_c->config.ins_data_dir, ins_idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        logerror(_("error for ins id:%d\n"), ci->ins_id);
        goto out;
    }

    if (libvirt_domain_active(ci->ins_domain)) {
        loginfo(_("instance %s is running already\n"), ci->ins_domain);
        ret = LY_S_FINISHED_INSTANCE_RUNNING;
        goto out_unlock;
    }

    snprintf(path, PATH_MAX, "%s/%d", g_c->config.ins_data_dir, ci->ins_id);
    if (ci->ins_status == DOMAIN_S_NEW || access(path, F_OK)) {
        /* prepare appliance */
        char app_idstr[10];
        snprintf(app_idstr, 10, "%d", ci->app_id);
        /* get lockfile for appliance */
        logdebug(_("trying to gain access to appliance %d ...\n"), ci->app_id);
        __send_response(g_c->wfd, ci, LY_S_RUNNING_WAITING);
        if (__file_lock_get(g_c->config.app_data_dir, app_idstr) < 0) {
            logerror(_("error in %s(%d).\n"), __func__, __LINE__);
            goto out_unlock;
        }
        /* prepare appliance dir */
        snprintf(path, PATH_MAX, "%s/%d", g_c->config.app_data_dir, ci->app_id);
        if (access(path, F_OK)) {
            if (mkdir(path, 0755) == -1) {
                logerror(_("can not create directory: %s\n"), path);
                logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
                __file_lock_put(g_c->config.app_data_dir, app_idstr);
                goto out_unlock;
            }
        }
        /* check whether to download appliance */
        snprintf(path, PATH_MAX, "%s/%d/%s", g_c->config.app_data_dir,
                                  ci->app_id, LUOYUN_APPLIANCE_FILE);
        int new_app = 1;
        if (access(path, F_OK) == 0) {
            loginfo(_("appliance %s found locally\n"), ci->app_name);
            loginfo(_("checking checksum ...\n"));
            __send_response(g_c->wfd, ci, LY_S_RUNNING_CHECKING_APP);
            if (lyutil_checksum(path, ci->app_checksum)) {
                logwarn(_("%s checksum(%s) failed. old appliance removed\n"),
                          ci->app_name, ci->app_checksum);
                unlink(path);
            }
            else
                new_app = 0;
        }
        /* download appliance */
        if (new_app) {
            ret = LY_S_FINISHED_FAILURE_APP_DOWNLOAD;
            loginfo(_("downloading %s from %s ...\n"), ci->app_name, ci->app_uri);
            __send_response(g_c->wfd, ci, LY_S_RUNNING_DOWNLOADING_APP);
            if (lyutil_download(ci->app_uri, path)) {
                logwarn(_("downloading %s from %s failed, %s.\n"), 
                           ci->app_name, ci->app_uri, "file not downloaded");
                unlink(path);
                __file_lock_put(g_c->config.app_data_dir, app_idstr);
                goto out_unlock;
            }
            if (access(path, F_OK)) {
                logerror(_("downloading %s from %s failed, %s.\n"),
                           ci->app_name, ci->app_uri, "file not exist");
                unlink(path);
                __file_lock_put(g_c->config.app_data_dir, app_idstr);
                goto out_unlock;
            }
            struct stat statbuf;
            if (stat(path, &statbuf)) {
                logerror(_("error in %s(%d), %s(%d).\n"), __func__, __LINE__,
                            strerror(errno), errno);
                unlink(path);
                __file_lock_put(g_c->config.app_data_dir, app_idstr);
                goto out_unlock;
            }
            if (statbuf.st_size < 1000000) {
                logerror(_("downloading %s from %s failed, %s.\n"),
                           ci->app_name, ci->app_uri, "file too small");
                unlink(path);
                __file_lock_put(g_c->config.app_data_dir, app_idstr);
                goto out_unlock;
            }
            loginfo(_("verifying checksum...\n"));
            __send_response(g_c->wfd, ci, LY_S_RUNNING_CHECKING_APP);
            if (lyutil_checksum(path, ci->app_checksum)) {
                logwarn(_("%s checksum(%s) failed.\n"), ci->app_name, ci->app_checksum);
                unlink(path);
                __file_lock_put(g_c->config.app_data_dir, app_idstr);
                goto out_unlock;
            }
            ret = -1;
        }
        /* done with appliance, release lock */
        if (__file_lock_put(g_c->config.app_data_dir, app_idstr) < 0) {
            logerror(_("error in %s(%d).\n"), __func__, __LINE__);
            logerror(_("error for ins id:%d, app_idstr: %s\n"), ci->ins_id, app_idstr);
            goto out_unlock;
        }
    }

    /* prepare instance dir */
    snprintf(path, PATH_MAX, "%s/%d", g_c->config.ins_data_dir, ci->ins_id);
    if (ci->ins_status == DOMAIN_S_NEW && access(path, F_OK) == 0) {
        logwarn(_("instance %d exists, clean it first\n"), ci->ins_id);
        if (__domain_dir_clean(path, 1) == -1) {
            logerror(_("can not clean dir for instance %d\n"), ci->ins_id);
            goto out_unlock;
        }
    }
    if (access(path, F_OK)) {
        if (mkdir(path, 0755) == -1) {
            logerror(_("can not create directory: %s\n"), path);
            logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
            goto out_unlock;
        }
    }
    else
        loginfo(_("instance %d exists\n"), ci->ins_id);

    /* prepare instance files */
    char path_ins[PATH_MAX];
    int ins_create_new = 0;
    snprintf(path_ins, PATH_MAX, "%s/%d/%s", g_c->config.ins_data_dir,
                                  ci->ins_id, LUOYUN_INSTANCE_DISK_FILE);
    if (access(path_ins, F_OK)) {
        ret = LY_S_FINISHED_FAILURE_APP_ERROR;
        ins_create_new = 1;
        snprintf(path, PATH_MAX, "%s/%d/%s", g_c->config.app_data_dir,
                                  ci->app_id, LUOYUN_APPLIANCE_FILE);
        loginfo(_("Extracting disk file\n"));
        __send_response(g_c->wfd, ci, LY_S_RUNNING_EXTRACTING_APP);
        int fd = creat(path_ins, S_IRUSR|S_IWUSR);
        if (fd < 0) {
            logerror(_("error creating file %s\n"), path_ins);
            logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
            goto out_insclean;
        }
        close(fd);
        if (lyutil_decompress_gz(path, path_ins)) {
            logwarn(_("decompress %s to %s failed.\n"), path, path_ins);
            unlink(path_ins);
            goto out_insclean;
        }
        if (access(path_ins, F_OK)) {
            logerror(_("instance disk file(%s) not exist\n"), path_ins);
            goto out_insclean;
        }
        ret = -1;
    }

    /* use disk offset to determine using xen or kvm */
    long long offset;
    offset = lyutil_get_disk_offset(path_ins);
    if (offset < 0) {
        logwarn(_("instance %d, get disk offset error\n"), ci->ins_id);
        goto out_insclean;
    }

    char * mount_path = NULL;
    snprintf(path, PATH_MAX, "%s/%d/kernel", g_c->config.ins_data_dir, ci->ins_id);
    if (offset == 0 && access(path, F_OK)) {
        /* mount instance image */
        __send_response(g_c->wfd, ci, LY_S_RUNNING_MOUNTING_IMAGE);
        char nametemp[32] = "/tmp/LuoYun_XXXXXX";
        mount_path = mkdtemp(nametemp);
        if (mount_path == NULL) {
            logerror(_("can not get a tmpdir for mount\n"));
            logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
            goto out_insclean;
        }
        snprintf(path, PATH_MAX, "%s/%d/%s", g_c->config.ins_data_dir, ci->ins_id,
                                  LUOYUN_INSTANCE_DISK_FILE);
        if (snprintf(tmpstr1024, 1024, "mount %s %s -o loop,offset=%lld",
                                        path, mount_path, offset) >= 1024) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            remove(mount_path);
            goto out_insclean;
        }
        if (system_call(tmpstr1024)) {
            logerror(_("failed executing %s\n"), tmpstr1024);
            remove(mount_path);
            goto out_insclean;
        }

        /* copy kernel/initrd, edit instance file, etc */
        __send_response(g_c->wfd, ci, LY_S_RUNNING_PREPARING_IMAGE);
        snprintf(path, PATH_MAX, "%s/%d", g_c->config.ins_data_dir, ci->ins_id);
        if (snprintf(tmpstr1024, 1024, "cp %s/$(readlink %s/kernel) %s/kernel",
                                        mount_path, mount_path, path) >= 1024) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto out_umount;
        }
        if (system_call(tmpstr1024)) {
            logerror(_("failed executing %s\n"), tmpstr1024);
            goto out_umount;
        }
        if (snprintf(tmpstr1024, 1024, "cp %s/$(readlink %s/initrd) %s/initrd",
                                        mount_path, mount_path, path) >= 1024) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto out_umount;
        }
        if (system_call(tmpstr1024)) {
            logerror(_("failed executing %s\n"), tmpstr1024);
            goto out_umount;
        }

        /* umount the instance image */
        __send_response(g_c->wfd, ci, LY_S_RUNNING_UNMOUNTING_IMAGE);
        snprintf(tmpstr1024, 1024, "umount %s", mount_path);
        if (system_call(tmpstr1024)) {
            logerror(_("can not umount %s\n"), mount_path);
            goto out_umount;
        }
        remove(mount_path);
        mount_path = NULL;
    }

    /* create instance config file */
    snprintf(path, PATH_MAX, "%s/%d/%s", g_c->config.ins_data_dir, ci->ins_id,
                              LUOYUN_INSTANCE_CONF_FILE);
#if 0
    int fd = creat(path, S_IRUSR|S_IWUSR);
    if (fd < 0) {
        logerror(_("error creating file %s\n"), path);
        logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
        goto out_insclean;
    }
    FILE * fp = fdopen(fd, "w");
    if (fp == NULL) {
        logerror(_("error opening file %s\n"), path);
        logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
        goto out_insclean;
    }
#else
    FILE * fp = __create_luoyun_ini(path);
    if (fp == NULL) {
        logerror(_("error opening file %s\n"), path);
        logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
        goto out_insclean;
    }
#endif
    int len = fprintf(fp,
                    "CLC_IP=%s\n"
                    "CLC_PORT=%d\n"
                    "CLC_MCAST_IP=%s\n"
                    "CLC_MCAST_PORT=%d\n"
                    "TAG=%d\n"
                    "KEY=%s\n"
                    "JSON=%s\n",
                    ci->osm_clcip,
                    ci->osm_clcport,
                    g_c->config.clc_mcast_ip,
                    g_c->config.clc_mcast_port,
                    ci->osm_tag,
                    ci->osm_secret,
                    ci->osm_json);
    if (len < 0) {
        logerror(_("error writing to %s\n"), path);
        logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
        fclose(fp);
        goto out_insclean;
    }
#if 0
    fclose(fp);
    if (truncate(path, ((len+1023)>>10)<<10)) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE_);
        logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
        goto out_insclean;
    }
#else
    if (__close_luoyun_ini(fp)) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        logerror(_("error: %d, %s\n"), errno, strerror(errno)); 
        unlink(path);
        goto out_insclean;
    }
#endif

    /* create xml */
    int fullvirt = 1;
    if (offset == 0)
        fullvirt = 0;
    char * xml = __domain_xml(ci, g_c->node->hypervisor, fullvirt);
    if (xml == NULL) {
        logerror(_("error creating domain xml\n"));
        goto out_insclean;
    }

    /* start instance */
    __send_response(g_c->wfd, ci, LY_S_RUNNING_STARTING_INSTANCE);
    ret = libvirt_domain_create(xml);
    if (ret < 0) {
        logerror(_("error start domain %s\n"), ci->ins_domain);
        free(xml);
        goto out_insclean;
    }
    free(xml);

    ret = LY_S_WAITING_STARTING_OSM;
    ly_node_send_report_resource();
    goto out_unlock;

out_umount:
    if (mount_path) {
        snprintf(tmpstr1024, 1024, "umount %s", mount_path);
        if (system_call(tmpstr1024)) {
            logerror(_("can not umount %s\n"), mount_path);
        }
        remove(mount_path);
    }
out_insclean:
    if (ret < 0 && ins_create_new) {
        snprintf(path, PATH_MAX, "%s/%d", g_c->config.ins_data_dir, ci->ins_id);
        __domain_dir_clean(path, 0); 
    }
out_unlock:
    if (__file_lock_put(g_c->config.ins_data_dir, ins_idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
    }
out:
    return ret;
}

static int __domain_stop(NodeCtrlInstance * ci)
{
    loginfo(_("%s is called\n"), __func__);

    char path_lock[PATH_MAX];
    if (snprintf(path_lock, PATH_MAX, "%s/%s",
                 g_c->config.node_data_dir, "instances") >= PATH_MAX) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    char idstr[10];
    snprintf(idstr, 10, "%d", ci->ins_id);

    int ret;
    __send_response(g_c->wfd, ci, LY_S_RUNNING_WAITING);
    logdebug(_("tring to gain access to instance files...\n"));
    if (__file_lock_get(path_lock, idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    if (libvirt_domain_active(ci->ins_domain) == 0) {
        loginfo(_("instance %s is not running.\n"), ci->ins_domain);
        ret = LY_S_FINISHED_INSTANCE_NOT_RUNNING;
        goto out;
    }
    ret = libvirt_domain_stop(ci->ins_domain);
    if (ret < 0) {
        logerror(_("stop domain %s failed\n"), ci->ins_domain);
        goto out;
    }
    __send_response(g_c->wfd, ci, LY_S_RUNNING_STOPPING);
    int wait = LY_NODE_STOP_INSTANCE_WAIT;
    while (wait > 0) {
        wait--;
        if (libvirt_domain_active(ci->ins_domain) == 0) {
            loginfo(_("instance %s stopped.\n"), ci->ins_domain);
            ret = LY_S_FINISHED_SUCCESS;
            goto out;
        }
        sleep(1);
    }
    if (libvirt_domain_poweroff(ci->ins_domain) == 0) {
        loginfo(_("instance %s forced off.\n"), ci->ins_domain);
        ret = LY_S_FINISHED_SUCCESS;
        goto out;
    }
    ret = LY_S_FINISHED_FAILURE;
out:
    if (__file_lock_put(path_lock, idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
    }

    if (ci->req_action == LY_A_NODE_STOP_INSTANCE && ret == LY_S_FINISHED_SUCCESS)
        ly_node_send_report_resource();
    return ret;
}

static int __domain_suspend(NodeCtrlInstance * ci)
{
    loginfo(_("%s: SUSPEND %s have not completed.\n"),
               __func__, ci->ins_domain);
    return -1;

}

static int __domain_save(NodeCtrlInstance * ci)
{
    loginfo(_("%s: SAVE % have not completed.\n"),
              __func__, ci->ins_domain);
    return -1;
}

static int __domain_acpireboot(NodeCtrlInstance * ci)
{
    loginfo(_("%s is called\n"), __func__);

    char path_lock[PATH_MAX];
    if (snprintf(path_lock, PATH_MAX, "%s/%s",
                 g_c->config.node_data_dir, "instances") >= PATH_MAX) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    char idstr[10];
    snprintf(idstr, 10, "%d", ci->ins_id);

    int ret;
    __send_response(g_c->wfd, ci, LY_S_RUNNING_WAITING);
    logdebug(_("tring to gain access to instance files...\n"));
    if (__file_lock_get(path_lock, idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    if (libvirt_domain_active(ci->ins_domain) == 0) {
        loginfo(_("instance %s is not running.\n"), ci->ins_domain);
        ret = LY_S_FINISHED_INSTANCE_NOT_RUNNING;
        goto out;
    }
    ret = libvirt_domain_reboot(ci->ins_domain);
    if (ret < 0) {
        logerror(_("reboot domain %s failed\n"), ci->ins_domain);
        ret = LY_S_FINISHED_FAILURE;
        goto out;
    }
    ret = LY_S_FINISHED_SUCCESS;
    sleep(LY_NODE_REBOOT_INSTANCE_WAIT);
out:
    if (__file_lock_put(path_lock, idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
    }
    return ret;
}

static int __domain_fullreboot(NodeCtrlInstance * ci)
{
    loginfo(_("%s is called\n"), __func__);
    int ret = __domain_stop(ci);
    if (ret == LY_S_FINISHED_INSTANCE_NOT_RUNNING || ret == LY_S_FINISHED_SUCCESS) {
        __send_response(g_c->wfd, ci, LY_S_RUNNING_STOPPED);
        ret = __domain_run(ci);
    }
    return ret;
}

static int __domain_destroy(NodeCtrlInstance * ci)
{
    loginfo(_("%s is called\n"), __func__);

    char path_lock[PATH_MAX];
    if (snprintf(path_lock, PATH_MAX, "%s/%s",
                 g_c->config.node_data_dir, "instances") >= PATH_MAX) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    char path_clean[PATH_MAX];
    if (snprintf(path_clean, PATH_MAX, "%s/%s/%d",
                 g_c->config.node_data_dir, "instances",
                 ci->ins_id) >= PATH_MAX) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    char idstr[10];
    snprintf(idstr, 10, "%d", ci->ins_id);

    int ret;
    logdebug(_("tring to gain access to instance files...\n"));
    if (__file_lock_get(path_lock, idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    if (libvirt_domain_active(ci->ins_domain)) {
        logwarn(_("instance %s is still running. stop it first\n"),
                   ci->ins_domain);
        ret = LY_S_FINISHED_INSTANCE_RUNNING;
        goto out;
    }
    if (access(path_clean, F_OK) != 0) {
        logwarn(_("instance %s not exist\n"), ci->ins_domain);
        /* ret = LY_S_FINISHED_INSTANCE_NOT_EXIST; */
        ret = 0;
        goto out;
    }
    ret = __domain_dir_clean(path_clean, 0);

    ly_node_send_report_resource();
out:
    if (__file_lock_put(path_lock, idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
    }
    return ret;
}

static int __domain_query(NodeCtrlInstance * ci)
{
    loginfo(_("%s is called\n"), __func__);

    char path[PATH_MAX];
    if (snprintf(path, PATH_MAX, "%s/%s/%d",
                 g_c->config.node_data_dir, "instances",
                 ci->ins_id) >= PATH_MAX) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }

    InstanceInfo ii;
    bzero(&ii, sizeof(InstanceInfo));
    if (libvirt_domain_active(ci->ins_domain))
        ii.status = DOMAIN_S_START;
    else if (access(path, F_OK) == 0)
        ii.status = DOMAIN_S_STOP;
    else
        ii.status = DOMAIN_S_NOT_EXIST;
    ii.id = ci->ins_id;

    LYReply r;
    r.req_id = ci->req_id;
    r.from = LY_ENTITY_NODE;
    r.to = LY_ENTITY_CLC;
    r.status = LY_S_FINISHED_SUCCESS;
    r.data = &ii;

    logdebug(_("sending instance query reply...\n"));
    char * xml = lyxml_data_reply_instance_info(&r, NULL, 0);
    if (xml == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }
    int ret = ly_packet_send(g_c->wfd, PKT_TYPE_CLC_INSTANCE_CONTROL_REPLY,
                             xml, strlen(xml));
    free(xml);
    if (ret < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        return -1;
    }

    return 0;
}

void * __instance_control_func(void * arg)
{
    NodeCtrlInstance * ci = arg;

    int ret = -1;

    loginfo(_("Start domain control, action = %d\n"), ci->req_action);

    switch (ci->req_action) {

    case LY_A_NODE_RUN_INSTANCE:
        ret = __domain_run(ci);
        break;

    case LY_A_NODE_STOP_INSTANCE:
        ret = __domain_stop(ci);
        break;

    case LY_A_NODE_SUSPEND_INSTANCE:
        ret = __domain_suspend(ci);
        break;

    case LY_A_NODE_SAVE_INSTANCE:
        ret = __domain_save(ci);
        break;

    case LY_A_NODE_ACPIREBOOT_INSTANCE:
        ret = __domain_acpireboot(ci);
        break;

    case LY_A_NODE_FULLREBOOT_INSTANCE:
        ret = __domain_fullreboot(ci);
        break;

    case LY_A_NODE_DESTROY_INSTANCE:
        ret = __domain_destroy(ci);
        break;

    case LY_A_NODE_QUERY_INSTANCE:
        ret = __domain_query(ci);
        goto done;

    default:
        logerror(_("unknown action: %d"), ci->req_action);
    }

    if (ret == 0)
        ret = __send_response(g_c->wfd, ci, LY_S_FINISHED_SUCCESS);
    else if (ret < 0)
        ret = __send_response(g_c->wfd, ci, LY_S_FINISHED_FAILURE);
    else
        ret = __send_response(g_c->wfd, ci, ret);

done:
    luoyun_node_ctrl_instance_cleanup(ci);
    free(ci);
    __update_thread_num(-1);
    logdebug(_("%s returns %d\n"), __func__, ret);
    return NULL;
}

int ly_handler_instance_control(NodeCtrlInstance * ci)
{
    if (ci == NULL || g_c == NULL || g_c->node == NULL)
        return -255;

    if (ci->req_action == LY_A_NODE_RUN_INSTANCE) {
        if (ly_handler_busy() || ly_node_busy()) {
            loginfo(_("node busy, drop request\n"));
            __send_response(g_c->wfd, ci, LY_S_FINISHED_FAILURE_NODE_BUSY);
            return 0;
        }
    }

    NodeCtrlInstance *arg = luoyun_node_ctrl_instance_copy(ci);
    if (arg == NULL)
        return -1;

#if 1
    pthread_attr_t attr;
    if (pthread_attr_init(&attr) != 0 || 
        pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED) != 0) {
        logerror(_("threading state config failed\n"));
        return -1;
    }

    pthread_t instance_tid;
    if (pthread_create(&instance_tid, &attr,
                       __instance_control_func, (void *)arg) != 0) {
        logerror(_("threading __instance_control_func failed\n"));
        return -1;
    }

    logdebug(_("start __instance_control_func in thread %d\n"), instance_tid);
    __update_thread_num(1);
    logdebug(_("__instance_control_func thread num is %d\n"), g_handler_thread_num);
#else
    __instance_control_func((void *)arg);
#endif

    return 0;
}
