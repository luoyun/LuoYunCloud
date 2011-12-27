#include <sys/socket.h>
#include <pthread.h>
#include "compute/handler.h"
#include "util/disk.h"

static int __send_respond (int socket, int status);

static int __domain_run (CpConfig *C, int id);
static int __domain_stop (CpConfig *C, int id);
static int __domain_suspend (CpConfig *C, int id);
static int __domain_save (CpConfig *C, int id);
static int __domain_reboot (CpConfig *C, int id);

static int __prepare_domain_env(CpConfig *C, int id);
static int __write_conf_to_img (CpConfig *C, int id);


/* Get the value of variable in a domain.conf like file,
 * save value string to varvalue buffer
 * Return 0 if OK, else are error. */
static int __read_config(const char *filename, const char *varname, char *varvalue, int maxlen)
{
     FILE *fp;
     fp = fopen(filename, "r");
     if ( fp == NULL )
     {
          logerror( _("Can not open config file: %s\n"), filename);
          return -1;
     }

     int ret = 0;
     int i, j, begin_tag, end_tag;
     char line[LY_LINE_MAX];
     char *kstr;
     char *vstr;

     varvalue[0] = '\0'; /* Init string */

     while ( 1 )
     {
          if ( fgets(line, LINE_MAX, fp ) == NULL )
               break;

          if ( str_filter_white_space(line) != 0 ) continue;

          vstr = strstr(line, "=");
          if ( vstr == NULL )
               continue;
          else
               vstr ++;

          if ( (kstr = strstr(line, varname)) != NULL )
          {
               begin_tag = end_tag = 0;
               j = 0;

               for (i = 0; i < maxlen && vstr[i] != '\0'; i++)
               {
                    if (vstr[i] == '\"')
                    {
                         if (begin_tag)
                              end_tag = 1;
                         else
                              begin_tag = 1;
                    }

                    else {
                         varvalue[j++] = vstr[i];
                    }
               }

               if (begin_tag)
                    if (!end_tag)
                    {
                         logerror(_("The \" in config file doest not match.\n"));
                         ret = -1;
                    }

               varvalue[j] = '\0';

               break;
          }
     }

     fclose(fp);
     return ret;
}


/* send respond to control server */
static int __send_respond (int socket, int status)
{
     LyRespond respond;
     respond.status = status;
     respond.length = 0;

     if(ly_send(socket, &respond, sizeof(LyRespond), 0, SEND_TIMEOUT))
     {
          logerror(_("Send domain control respond failed.\n"));
          return -1;
     }

     return 0;
}



static int __domain_run(CpConfig *C, int id)
{
     logdebug(_("START %s\n"), __func__);

     int fd;
     
     // save the current dir
     if ((fd = open(".", O_RDONLY)) < 0)
     {
          logerror(_("Open current dir failed.\n"));
          return -1;
     }

     char lpath[LY_PATH_MAX];
     snprintf(lpath, LY_PATH_MAX, "%s/%d", C->root_path, id);

     lyu_make_sure_dir_exist(lpath);

     if (chdir(lpath) < 0)
     {
          logerror(_("Change working directory to %s failed.\n"), lpath);
          return -1;
     }

     int ret = 0;

     if (__prepare_domain_env(C, id))
          logdebug(_("Prepare domain environment failed.\n"));
     else {
          char libvirtd_conf[] = LIBVIRTD_CONFIG;
          char *xml = file2str(libvirtd_conf);

          virDomainPtr domain;

          domain = create_transient_domain(C->conn, xml);

          free(xml);

          if ( domain == NULL )
               ret = -1;
     }


     if (fchdir(fd) < 0)
     {
          logdebug(_("Restore working directory failed.\n"));
          ret = -1;
     }

     return ret;
}



static int __domain_stop (CpConfig *C, int id)
{
     logdebug("%s: STOP domian %d.\n", __func__, id);

     char dconf[LY_PATH_MAX];
     snprintf(dconf, LY_PATH_MAX, "%s/%d/%s", C->root_path, id, DOMAIN_CONFIG_FILE);

     if ( file_exist(dconf) )
     {
          logdebug(_("%s does not exist.\n"), dconf);
          return -1;
     }

     char name[LY_NAME_MAX];
     if(__read_config(dconf, "NAME", name, LY_NAME_MAX))
     {
          logerror(_("Get value of NAME from %s failed.\n"), dconf);
          return -1;
     }


     if (domain_stop (C->conn, name))
     {
          logerror(_("Stop domain \"%s\"[%d] failed.\n"), name, id);
          return -1;
     }

     logerror(_("Stop domain \"%s\"[%d] success.\n"), name, id);

     return 0;
}



static int __domain_suspend(CpConfig *C, int id)
{
     loginfo(_("%s: SUSPEND %d have not completed.\n"), __func__, id);
     return -1;

}

static int __domain_save(CpConfig *C, int id)
{
     loginfo(_("%s: SAVE %d have not completed.\n"), __func__, id);
     return -1;
}

static int __domain_reboot(CpConfig *C, int id)
{
     loginfo(_("%s: REBOOT %d have not completed.\n"), __func__, id);
     return -1;
}

static int __prepare_domain_env(CpConfig *C, int id)
{
     logdebug(_("Prepare domian environment.\n"));

     int ret;
     char uri[LY_PATH_MAX];

     // Prepare domain.conf
     char domain_conf[] = "domain.conf";

     if ( !file_exist(domain_conf) )
          logdebug(_("%s exist, skeep download.\n"), domain_conf);
     else {
          snprintf(uri, LY_PATH_MAX, DOMAIN_CONFIG_URI_TEMP, id);
          if ( 0 != ly_dl(uri, domain_conf) )
               return -1;
     }


     // Prepare config of libvirtd
     char libvirtd_conf[] = "domain_libvirtd.xml";
     if ( !file_exist(libvirtd_conf) )
          logdebug(_("%s exist, skeep download.\n"), libvirtd_conf);
     else {
          ret = __read_config(domain_conf, "IMAGE_LIBVIRTD_CONFIG_URI", uri, LY_PATH_MAX);
          if (ret)
          {
               logerror(_("Get value of IMAGE_LIBVIRTD_CONFIG_URI from %s failed.\n"), uri);
               return -1;
          }

          //logdebug(_("IMAGE_LIBVIRTD_CONFIG_URI: \"%s\"\n"), uri);

          if ( 0 != ly_dl(uri, libvirtd_conf) )
               return -1;
     }


     // Prepare boot disk
     char boot_disk_gz[] = OS_DISK_FILE_GZ;
     char boot_disk[] = OS_DISK_FILE;
     if ( !file_exist(boot_disk) )
     {
          logdebug(_("%s exist. skeep download.\n"), boot_disk);
          // TODO: should check md5sum
     }
     else {
          // GET IMAGE URI
          ret = __read_config(domain_conf, "IMAGE_URI", uri, LY_PATH_MAX);
          if (ret)
          {
               logerror(_("Get value of IMAGE_URI from %s failed.\n"), domain_conf);
               return -1;
          }

          //logdebug(_("IMAGE_URI: \"%s\"\n"), uri);

          if ( 0 != ly_dl(uri, boot_disk_gz) )
               return -1;

          //if (0 != lyu_decompress_bzip2(compress_img_path,
          //                             decompress_img_path))
          if (0 != lyu_decompress_gz(boot_disk_gz, boot_disk))
          {
               logerror(_("Decompress %s failed.\n"), boot_disk_gz);
               return -1;
          }

     }

     // write the dynamic conf to disk img
     __write_conf_to_img(C, id);

     // TODO: auto create conf file by DomainInfo

     return 0;
}


/* Write the dynamic configure to img file */
static int __write_conf_to_img (CpConfig *C, int id)
{
     int ret = -1;

     char nametemp[32] = "/tmp/LuoYun_XXXXXX";
     char *mount_path;
     mount_path = mkdtemp(nametemp);
     if (mount_path == NULL)
     {
          logerror(_("Can not get a tmpdir for mount_path"));
          return -1;
     }

     if ( lyu_make_sure_dir_exist(mount_path) != 0 )
          goto clean2;

     char boot_disk[] = OS_DISK_FILE;
     unsigned long long offset;
     offset = dk_get_boot_offset(boot_disk);
     if (offset <= 0)
          goto clean2;

     // TODO: should not use system call !
     char buf[1024];

     sprintf(buf, "mount -o loop,offset=%lld %s %s",
             offset, boot_disk, mount_path);
     if ( lyu_system_call(buf) )
          goto clean2;

     sprintf(buf, "%s/LuoYun/", mount_path);
     if ( lyu_make_sure_dir_exist(buf) != 0 )
          goto clean;

     // GET the config of domain
     // TODO: make sure it was modified.
     sprintf(buf, "%s/LuoYun/LuoYun.conf", mount_path);
     // Download LuoYun.conf
     char uri[LY_PATH_MAX];
     char domain_conf[] = "domain.conf";
     ret = __read_config(domain_conf, "OSMANAGER_CONFIG", uri, LY_PATH_MAX);
     if (ret)
     {
          logerror(_("Get value of OSMANAGER_CONFIG from %s failed.\n"), domain_conf);
          goto clean;
     }

     if ( 0 != ly_dl(uri, buf) )
          ret = -1;


clean:
     sprintf(buf, "umount %s", mount_path);
     if ( lyu_system_call(buf) )
     {
          logerror(_("Umount %s error.\n"), mount_path);
          ret = -1;
     }

     if ( rmdir(mount_path) )
     {
          logerror(_("Remove directory \"%s\' error"), mount_path);
          ret = -1;
     }

clean2:
     //free(mount_path);
     return ret;
}



int hl_domain_control(CpConfig *C,
                      int S, /* socket */
                      int datalen /* request data length */)
{
     loginfo("START %s\n", __func__);

     int ret = -1;

     if (C == NULL)
     {
          logerror(_("CpConfig is NULL\n"));
          return __send_respond(S, RESPOND_STATUS_FAILED);
     }

     DomainControlData D;


     if (datalen != sizeof(D))
     {
          logerror(_("Can not found DomainControlData: (%d) != (%d)\n"), datalen, sizeof(D));
          return __send_respond(S, RESPOND_STATUS_FAILED);
     }

     ret = recv(S, &D, sizeof(D), 0);
     if ( ret != sizeof(D) )
     {
          logerror(_("Recv request data failed: (%d) != (%d)\n"), ret, sizeof(D));
          return __send_respond(S, RESPOND_STATUS_FAILED);
     }

     logdebug(_("Start domain control, action = %d\n"), D.action);

     switch (D.action) {

     case LA_DOMAIN_RUN:
          ret = __domain_run(C, D.id);
          break;

     case LA_DOMAIN_STOP:
          ret = __domain_stop(C, D.id);
          break;

     case LA_DOMAIN_SUSPEND:
          ret = __domain_suspend(C, D.id);
          break;

     case LA_DOMAIN_SAVE:
          ret = __domain_save(C, D.id);
          break;

     case LA_DOMAIN_REBOOT:
          ret = __domain_reboot(C, D.id);
          break;

     default:
          logerror(_("unknown action: %d"), D.action);

     }

     if (ret)
          return __send_respond(S, RESPOND_STATUS_FAILED);
     else
          return __send_respond(S, RESPOND_STATUS_OK);
}


