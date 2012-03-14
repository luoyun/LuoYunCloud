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
    if (access(lock_dir,  R_OK | W_OK | X_OK | F_OK) != 0)
        return -1;
    char path[PATH_MAX];
    if (snprintf(path, PATH_MAX, "%s/.forlock", lock_dir) >= PATH_MAX)
        return -1;
    int fd = creat(path, S_IWUSR);
    if (fd < 0 ){
        return -1;
    }
    close(fd);
    char link_path[PATH_MAX];
    if (snprintf(link_path, PATH_MAX, "%s/.forlock.%s",
                 lock_dir, lock_ext) >= PATH_MAX)
        return -1;
    int time_warn = 30; 
    while (link(path, link_path) < 0) {
        /* someone has the lock already */
        if (time_warn == 0) {
            logwarn(_("waited thread lock for 30 seconds."
                      "continue waiting...\n"));
            time_warn = 30;
        }
        sleep(1);
        time_warn--;
    }
    return 0; /* lock granted */
}
        
static int __file_lock_put(char * lock_dir, char * lock_ext)
{
    if (lock_dir == NULL)
        return -1;
    if (access(lock_dir,  R_OK | W_OK | X_OK | F_OK) != 0)
        return -1;
    char link_path[PATH_MAX];
    if (snprintf(link_path, PATH_MAX, "%s/.forlock.%s",
                 lock_dir, lock_ext) >= PATH_MAX)
        return -1;
    if (unlink(link_path) < 0)
        return -1;
    return 0; /* lock released */
}

static int __domain_dir_clean(char * dir, int keepdir)
{
    if (dir == NULL)
        return -1;

    int ret = -1;

    /* save the current dir */
    int olddir = -1;
    if ((olddir = open(".", O_RDONLY)) < 0) {
        logerror(_("open current dir failed.\n"));
        return -1;
    }

    if (chdir(dir) < 0) {
        logerror(_("change working directory to %s failed.\n"), dir);
        goto out;
    }
    char * file = LUOYUN_INSTANCE_DISK_FILE;
    if (access(file, R_OK) == 0 && unlink(file) != 0) {
        logerror(_("removing %s failed.\n"), file);
        goto out;
    }
    file = "kernel";
    if (access(file, R_OK) == 0 && unlink(file) != 0) {
        logerror(_("removing %s failed.\n"), file);
        goto out;
    }
    file = "initrd";
    if (access(file, R_OK) == 0 && unlink(file) != 0) {
        logerror(_("removing %s failed.\n"), file);
        goto out;
    }
    if (fchdir(olddir) < 0) {
       logerror(_("restore working directory failed.\n"));
       ret = -1;
    }
    close(olddir);

    if (keepdir)
        return 0;

    if (rmdir(dir) != 0) {
        logerror(_("error removing %s, err %d\n"), dir, errno);
        goto out;
    }

    return 0;
out:
    return ret;
}

static char * __domain_xml(NodeCtrlInstance * ci, int hypervisor, int fullvirt)
{
    if (ci == NULL || g_c == NULL)
        return NULL;

    char * path = malloc(PATH_MAX);
    if (path == NULL)
        return NULL;
    if (snprintf(path, PATH_MAX, "%s/%s/%d",
                 g_c->config.node_data_dir, "instances",
                 ci->ins_id) >= PATH_MAX) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        free(path);
        return NULL;
    }

    int size = LIBVIRT_XML_DATA_MAX;
    char * buf = malloc(size);
    if (buf == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        free(path);
        return NULL;
    }

    int len = -1;
    if (hypervisor == HYPERVISOR_IS_KVM) {
        len = snprintf(buf, size, LIBVIRT_XML_TMPL_KVM, 
                       ci->ins_id, ci->ins_name,
                       ci->ins_mem, ci->ins_vcpu, path, ci->ins_mac);
    }
    else if (hypervisor == HYPERVISOR_IS_XEN && fullvirt) {
        len = -2;
    }
    else if (hypervisor == HYPERVISOR_IS_XEN && fullvirt == 0) {
        char ins_name[20];
        snprintf(ins_name, 20, "i-%d", ci->ins_id);
        len = snprintf(buf, size, LIBVIRT_XML_TMPL_XEN_PARA, 
                       ci->ins_id, ins_name, path, path,
                       ci->ins_mem, ci->ins_vcpu, path, ci->ins_mac);
    }
    logsimple("%d\n", len);
    if (len < 0 || len >= size) {
        free(path);
        free(buf);
        return NULL;
    }
    logsimple("%s\n", buf);

    free(path);
    return buf;
}

static int __domain_run_data_check(NodeCtrlInstance * ci)
{
    if (ci == NULL || g_c == NULL)
        return -255;

    if (ci->ins_vcpu == 0)
        ci->ins_vcpu = LUOYUN_INSTANCE_CPU_DEFAULT;
    if (ci->ins_mem == 0)
        ci->ins_mem = LUOYUN_INSTANCE_MEM_DEFAULT;
    if (ci->ins_mac == NULL)
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
    char * path_lock = malloc(PATH_MAX);
    char * path = malloc(PATH_MAX);
    char * tmpstr1024 = malloc(1024);
    if (path_lock == NULL || path == NULL || tmpstr1024 == NULL) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out;
    }

    /* appliances and instances are expected sub-dir */
    char * appdir = "appliances";
    char * insdir = "instances";

    if (snprintf(path_lock, PATH_MAX, "%s/%s",
                 g_c->config.node_data_dir, insdir) >= PATH_MAX) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out;
    }
    char ins_idstr[10];
    snprintf(ins_idstr, 10, "%d", ci->ins_id);

    logdebug(_("tring to gain access to instance files...\n"));
    __send_response(g_c->wfd, ci, LY_S_RUNNING_WAITING);
    if (__file_lock_get(path_lock, ins_idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out;
    }

    if (libvirt_domain_active(ci->ins_name)) {
        loginfo(_("instance %s is running already\n"), ci->ins_name);
        ret = LY_S_FINISHED_INSTANCE_RUNNING;
        goto out_unlock;
    }

    /* save the current dir */
    int olddir = -1;
    if ((olddir = open(".", O_RDONLY)) < 0) {
        logerror(_("open current dir failed.\n"));
        goto out_unlock;
    }

    /* change to data root dir */
    char * curdir = g_c->config.node_data_dir;
    if (chdir(curdir) < 0) {
        logerror(_("change working directory to %s failed.\n"), curdir);
        goto out_unlock;
    }

    /* work in appliances dir */
    char app_idstr[10];
    if (snprintf(app_idstr, 10, "%d", ci->app_id) >= 10 ) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out_chdir;
    }
    if (chdir(appdir) < 0) {
        logerror(_("change working directory to %s failed.\n"), appdir);
        goto out_chdir;
    }
    logdebug(_("tring to gain access to appliance file...\n"));
     __send_response(g_c->wfd, ci, LY_S_RUNNING_WAITING);
    if (__file_lock_get(".", app_idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out_chdir;
    }
    if (access(app_idstr, F_OK)) {
        if (mkdir(app_idstr, 0755) == -1) {
            logerror(_("can not create directory: %s\n"), app_idstr);
            __file_lock_put(".", app_idstr);
            goto out_chdir;
        }
    }
    if (chdir(app_idstr) < 0) {
        logerror(_("change working directory to %s failed.\n"), app_idstr);
        __file_lock_put("..", app_idstr);
        goto out_chdir;
    }
    if (access(ci->app_name, F_OK)) {
        loginfo(_("downloading %s from %s ...\n"), ci->app_name, ci->app_uri);
        __send_response(g_c->wfd, ci, LY_S_RUNNING_DOWNLOADING_APP);
        if (lyutil_download(ci->app_uri, ci->app_name)) {
            logwarn(_("downloading %s from %s failed.\n"), 
                       ci->app_name, ci->app_uri);
            unlink(ci->app_name);
            __file_lock_put("..", app_idstr);
            goto out_chdir;
        }
    }
    else
        loginfo(_("appliance %s found locally\n"), ci->app_name);
    loginfo(_("checking checksum ...\n"));
    __send_response(g_c->wfd, ci, LY_S_RUNNING_CHECKING_APP);
    if (lyutil_checksum(ci->app_name, ci->app_checksum)) {
        logwarn(_("%s checksum(%s) failed.\n"), ci->app_name, ci->app_checksum);
        unlink(ci->app_name);
        __file_lock_put("..", app_idstr);
        goto out_chdir;
    }
    if (__file_lock_put("..", app_idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out_chdir;
    }
    if (chdir("../..") < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out_chdir;
    }

    if (chdir(insdir) < 0) {
        logerror(_("change working directory to %s failed.\n"), insdir);
        goto out_chdir;
    }

    /* prepare instance dir */
    if (ci->ins_status == DOMAIN_S_NEW && access(ins_idstr, F_OK) == 0) {
        logwarn(_("instance %d exists, clean it first\n"), ci->ins_id);
        if (__domain_dir_clean(ins_idstr, 1) == -1) {
            logerror(_("can not clean dir for instance %d\n"), ci->ins_id);
            goto out_chdir;
        }
    }
    if (access(ins_idstr, F_OK)) {
        if (mkdir(ins_idstr, 0755) == -1) {
            logerror(_("can not create dir for instance %d\n"), ci->ins_id);
            goto out_chdir;
        }
    }
    else
        loginfo(_("instance %d exists\n"), ci->ins_id);

    if (chdir(ins_idstr) < 0) {
        logerror(_("change directory to instance %d failed.\n"), ci->ins_id);
        goto out_chdir;
    }

    /* from now on, work in the instance dir */
    int ins_create_new = 0;
    if (access(LUOYUN_INSTANCE_DISK_FILE, F_OK)) {
        ins_create_new = 1;
        if (snprintf(path, PATH_MAX, 
                    "../../appliances/%d/%s", ci->app_id, ci->app_name) >=
                    PATH_MAX) {
            logerror(_("path error in %s(%d)\n"), __func__, __LINE__);
            goto out_chdir;
        }
        loginfo(_("Extracting disk file\n"));
        __send_response(g_c->wfd, ci, LY_S_RUNNING_EXTRACTING_APP);
        if (lyutil_decompress_gz(path, LUOYUN_INSTANCE_DISK_FILE)) {
            logwarn(_("decompress %s failed.\n"), path);
            unlink(path);
            goto out_insclean;
        }
        if (access(LUOYUN_INSTANCE_DISK_FILE, F_OK)) {
            logerror(_("instance(%d) disk file not exist\n"), ci->ins_id);
            goto out_insclean;
        }
    }

    /* mount instance image */
    __send_response(g_c->wfd, ci, LY_S_RUNNING_MOUNTING_IMAGE);
    long long offset;
    offset = lyutil_get_disk_offset(LUOYUN_INSTANCE_DISK_FILE);
    if (offset < 0) {
        logwarn(_("instance %d, get disk offset error\n"), ci->ins_id);
        goto out_insclean;
    }
    char nametemp[32] = "/tmp/LuoYun_XXXXXX";
    char * mount_path = mkdtemp(nametemp);
    if (mount_path == NULL) {
        logerror(_("can not get a tmpdir for mount\n"));
        goto out_insclean;
    }
    if (snprintf(tmpstr1024, 1024, "mount %s %s -o loop,offset=%lld",
                 LUOYUN_INSTANCE_DISK_FILE, mount_path, offset) >= 1024) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out_insclean;
    }
    if (system_call(tmpstr1024)) {
        logerror(_("failed executing %s\n"), tmpstr1024);
        remove(mount_path);
        goto out_insclean;
    }

    __send_response(g_c->wfd, ci, LY_S_RUNNING_PREPARING_IMAGE);
    /* copy kernel/initrd, edit instance file, etc */
    if ((access("kernel", F_OK) || access("initrd", F_OK)) && offset == 0) {
        if (snprintf(tmpstr1024, 1024, "cp %s/$(readlink %s/kernel) kernel",
                     mount_path, mount_path) >= 1024) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto out_umount;
        }
        if (system_call(tmpstr1024)) {
            logerror(_("failed executing %s\n"), tmpstr1024);
            goto out_umount;
        }
        if (snprintf(tmpstr1024, 1024, "cp %s/$(readlink %s/initrd) initrd",
                     mount_path, mount_path) >= 1024) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto out_umount;
        }
        if (system_call(tmpstr1024)) {
            logerror(_("failed executing %s\n"), tmpstr1024);
            goto out_umount;
        }
    }
    if (snprintf(path, PATH_MAX, "%s/%s", mount_path,
                 g_c->config.osm_conf_path) >= PATH_MAX) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out_umount;
    }
    if (lyutil_create_file(path, 1) < 0) {
        logerror(_("failed creating file %s\n"), path);
        goto out_umount;
    }
    if (snprintf(tmpstr1024, 1024,
                 "CLC_IP=%s\nCLC_PORT=%d\n"
                 "CLC_MCAST_IP=%s\nCLC_MCAST_PORT=%d\n"
                 "STORAGE_IP=%s\nSTORAGE_METHOD=%d\nSTORAGE_PARM=%s\n"
                 "TAG=%d\n",
                 ci->osm_clcip, ci->osm_clcport,
                 g_c->config.clc_mcast_ip, g_c->config.clc_mcast_port,
                 ci->storage_ip ? ci->storage_ip : "",
                 ci->storage_method,
                 ci->storage_parm ? ci->storage_parm : "",
                 ci->osm_tag) >= 1024) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out_umount;
    }
    int fh = creat(path, S_IRUSR);
    if (fh < 0) {
        logerror(_("error writing to %s\n"), path);
        goto out_umount;
    }
    if (write(fh, tmpstr1024, strlen(tmpstr1024)) < 0) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__, errno);
        close(fh);
        goto out_umount;
    }
    close(fh);
    if (ci->ins_status == DOMAIN_S_NEW) {
        if (snprintf(path, PATH_MAX, "%s/%s", mount_path,
                     g_c->config.osm_key_path) >= PATH_MAX) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__);
            goto out_umount;
        }
        fh = creat(path, S_IRUSR);
        if (fh < 0) {
            logerror(_("error writing to %s\n"), path);
            goto out_umount;
        }
        if (write(fh, ci->osm_secret, strlen(ci->osm_secret)) < 0) {
            logerror(_("error in %s(%d)\n"), __func__, __LINE__, errno);
            close(fh);
            goto out_umount;
        }
        close(fh);
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
    virDomainPtr domain;
    domain = libvirt_domain_create(xml);
    free(xml);
    if (domain == NULL) {
        logerror(_("error start domain %s\n"), ci->ins_name);
        goto out_insclean;
    }

    ret = LY_S_WAITING_STARTING_OSM;
    goto out_chdir;

out_umount:
    if (mount_path) {
        snprintf(tmpstr1024, 1024, "umount %s", mount_path);
        if (system_call(tmpstr1024)) {
            logerror(_("can not umount %s\n"), mount_path);
        }
        remove(mount_path);
    }
out_insclean:
    if (chdir("..") < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
        goto out;
    }
    if (ret < 0 && ins_create_new) {
        __domain_dir_clean(ins_idstr, 0); 
    }
out_chdir:
    if (fchdir(olddir) < 0) {
       logdebug(_("Restore working directory failed.\n"));
    }   
    close(olddir);
out_unlock:
    if (__file_lock_put(path_lock, ins_idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
    }
out:
    if (path_lock)
        free(path_lock);
    if (path)
        free(path);
    if (tmpstr1024)
        free(tmpstr1024);
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
    if (libvirt_domain_active(ci->ins_name) == 0) {
        loginfo(_("instance %s is not running.\n"), ci->ins_name);
        ret = LY_S_FINISHED_INSTANCE_NOT_RUNNING;
        goto out;
    }
    ret = libvirt_domain_stop(ci->ins_name);
    if (ret < 0) {
        logerror(_("stop domain %s failed\n"), ci->ins_name);
        goto out;
    }
    int wait = LY_NODE_STOP_INSTANCE_WAIT;
    while (wait > 0) {
        wait--;
        if (libvirt_domain_active(ci->ins_name) == 0) {
            loginfo(_("instance %s stopped.\n"), ci->ins_name);
            ret = LY_S_FINISHED_SUCCESS;
            goto out;
        }
        sleep(1);
    }
    if (libvirt_domain_poweroff(ci->ins_name) == 0) {
        loginfo(_("instance %s forced off.\n"), ci->ins_name);
        ret = LY_S_FINISHED_SUCCESS;
        goto out;
    }
    ret = LY_S_FINISHED_FAILURE;
out:
    if (__file_lock_put(path_lock, idstr) < 0) {
        logerror(_("error in %s(%d).\n"), __func__, __LINE__);
    }

    return ret;
}

static int __domain_suspend(NodeCtrlInstance * ci)
{
    loginfo(_("%s: SUSPEND %s have not completed.\n"), __func__,
              ci->ins_name);
    return -1;

}

static int __domain_save(NodeCtrlInstance * ci)
{
    loginfo(_("%s: SAVE % have not completed.\n"), __func__,
              ci->ins_name);
    return -1;
}

static int __domain_reboot(NodeCtrlInstance * ci)
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
    if (libvirt_domain_active(ci->ins_name) == 0) {
        loginfo(_("instance %s is not running.\n"), ci->ins_name);
        ret = LY_S_FINISHED_INSTANCE_NOT_RUNNING;
        goto out;
    }
    ret = libvirt_domain_reboot(ci->ins_name);
    if (ret < 0) {
        logerror(_("reboot domain %s failed\n"), ci->ins_name);
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
    if (libvirt_domain_active(ci->ins_name)) {
        logwarn(_("instance %s is still running. stop it first\n"), ci->ins_name);
        ret = LY_S_FINISHED_INSTANCE_RUNNING;
        goto out;
    }
    if (access(path_clean, F_OK) != 0) {
        logwarn(_("instance %s not exist\n"), ci->ins_name);
        ret = LY_S_FINISHED_INSTANCE_NOT_EXIST;
        goto out;
    }
    ret = __domain_dir_clean(path_clean, 0);

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
    if (libvirt_domain_active(ci->ins_name))
        ii.status = DOMAIN_S_START;
    else if (access(path, F_OK) == 0)
        ii.status = DOMAIN_S_STOP;
    else
        ii.status = DOMAIN_S_NOT_EXIST;

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

    case LY_A_NODE_REBOOT_INSTANCE:
        ret = __domain_reboot(ci);
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

    pthread_t instance_tid;
    if (pthread_create(&instance_tid, NULL,
                       __instance_control_func, (void *)arg) != 0) {
        logerror(_("threading __instance_control_func failed\n"));
        return -1;
    }
   
    logdebug(_("start __instance_control_func in thread %d\n"), instance_tid);
    __update_thread_num(1);
    logdebug(_("__instance_control_func thread num is %d\n"), g_handler_thread_num);
    return 0;
}
