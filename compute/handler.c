#include <sys/socket.h>
#include <pthread.h>
#include "compute/handler.h"
#include "util/disk.h"


static int __send_respond (int socket, int status);
static int __send_request (int socket, int action,
                           int datalen, void *data);
static int __get_respond (int socket,
                          LySockRespond *respond,
                          int datalen,
                          void *data );

static int __tell_control_server (LyComputeServerConfig *sc,
                                  int action,
                                  int datalen,
                                  void *data);

static void *__domain_control ( void *arg );
static void __domain_run (DomainControlHandler *DCH);
static void __domain_stop (DomainControlHandler *DCH);
static void __domain_suspend (DomainControlHandler *DCH);
static void __domain_save (DomainControlHandler *DCH);
static void __domain_reboot (DomainControlHandler *DCH);

static int __prepare_domain_env(DomainControlHandler *DCH,
                                char *conf_path);

static int __write_conf_to_img (DomainControlHandler *DCH,
                                char *img_path);

/* send request to control server */
static int
__send_request ( int sk, int action,
                 int datalen, void *data )
{
     LySockRequest request;
     request.from = LST_COMPUTE_S;
     request.to = LST_CONTROL_S;
     request.type = 0;
     request.action = action;
     request.datalen = datalen;

     int err;
     err = send(sk, &request, sizeof(LySockRequest), 0);
     if (datalen)
          err += send(sk, data, datalen, 0);

     if ( -1 == err )
     {
          logprintfl(LYERROR, "%s: send request err\n",
                     __func__);
          return -2;
     }

     return 0;
}


/* send request to control server */
static int
__get_respond ( int sk, LySockRespond *respond,
                int datalen, void *data )
{
     int recvlen;
     recvlen = recv(sk, respond, sizeof(LySockRespond), 0);
     if (recvlen != sizeof(LySockRespond))
     {
          logprintfl(LYERROR, "%s: read respond err\n",
                     __func__);
          return -1;
     }

     // TODO: check respond is correct or not.

     if (!datalen)
          return 0;

     if (respond->datalen != datalen)
     {
          logprintfl(LYERROR, "%s: datalen not match, "
                     "respond->datalen = %d, but your "
                     "want %d\n", respond->datalen,
                     datalen);
          return -2;
     }

     recvlen = recv(sk, data, datalen, 0);
     if (recvlen != datalen)
     {
          logprintfl(LYERROR, "%s: read respond data err, "
                     "recvlen = %d, datalen = %d\n",
                     __func__, recvlen, datalen);
          return -3;
     }

     return 0;
}


static int
__tell_control_server ( LyComputeServerConfig *sc, int action,
                        int datalen, void *data )
{
     logdebug("%s:%d:%s tell control server, uid=%d, gid=%d\n",
              __FILE__, __LINE__, __func__, getuid(), getgid());

     int sk, err;
     sk = connect_to_host(sc->cts_ip, sc->cts_port);
     if ( sk <= 0 ) return -1;

     err = __send_request(sk, action, datalen, data);

     //TODO: read the respond

     close(sk);
     return err;
}

/* send respond to control server */
static int
__send_respond (int socket, int status)
{

     LySockRespond respond;
     respond.status = status;
     respond.from = LST_COMPUTE_S;
     respond.to = LST_CONTROL_S;
     respond.used_time = 0;
     respond.datalen = 0;

     int err;

     err = send(socket, &respond, sizeof(LySockRespond), 0);
     if ( -1 == err )
     {
          logprintfl(LYERROR, "%s: could not send respond "
                     "to control server\n", __func__);
     } else {
          logprintfl(LYDEBUG, "%s: send respond to control "
                     "server success, status = %d\n",
                     __func__, status);
     }

     return err;
}


int
hl_control_domain ( LyComputeServerConfig *sc,
                    LySockRequestHandler *RH )
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

     if (RH->request->datalen <= 0)
     {
          logprintfl(LYERROR,
                     "%s:%d:%s => request format err,"
                     "datalen = %d\n",
                     __FILE__, __LINE__, __func__,
                     RH->request->datalen);
          return -1;
     }

     DomainInfo *dip;
     dip = malloc( sizeof(DomainInfo) );
     if ( dip == NULL )
     {
          logprintfl(LYERROR, "%s: malloc dip err\n",
                     __func__);
          return -2;
     }

     int recvlen;
     recvlen = recv(RH->sk, dip, sizeof(DomainInfo), 0);
     if ( recvlen != sizeof(DomainInfo) )
     {
          logprintfl(LYERROR, "get request data error,"
                     " read len = %d, data len = %d\n",
                     recvlen, sizeof(DomainInfo));
          free(dip);
          return -2;
     }

     logprintfl(LYDEBUG, "LA_CONTROL_DOMAIN: id = %d\n",
                dip->id);


     // do domain control
     DomainControlHandler *DCH;
     DCH = malloc(sizeof(DomainControlHandler));
     if (DCH == NULL)
     {
          logprintfl(LYERROR, "%s: malloc dip err\n",
                     __func__);
          free(dip);
          return -3;
     }
     DCH->sc = sc;
     DCH->action = RH->request->action;
     DCH->dip = dip;
     pthread_t domain_control_tid;
     int status = pthread_create(&domain_control_tid, NULL,
                                 __domain_control, DCH);

     status = __send_respond(RH->sk, status);
     //free(dip);
     return status;
}


void *
__domain_control(void *arg)
{
     DomainControlHandler *DCH;
     DCH = (DomainControlHandler *) arg;

     switch (DCH->action) {
     case LA_DOMAIN_RUN:
          __domain_run(DCH);
          break;
     case LA_DOMAIN_STOP:
          __domain_stop(DCH);
          break;
     case LA_DOMAIN_SUSPEND:
          __domain_suspend(DCH);
          break;
     case LA_DOMAIN_SAVE:
          __domain_save(DCH);
          break;
     case LA_DOMAIN_REBOOT:
          __domain_reboot(DCH);
          break;
     default:
          logprintfl(LYERROR, "%s: unknown action of request",
                     __func__);
     }

     free(DCH->dip);
     free(DCH);
     pthread_exit((void *)0);
}


static void __domain_run (DomainControlHandler *DCH)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

     //lyu_print_compute_server_config(DCH->sc);

     char conf_path[LINE_MAX] = {'\0'};
     int err;
     err = __prepare_domain_env(DCH, conf_path);
     // TODO: check it
     if (err != 0 || *conf_path == '\0')
     {
          logprintfl(LYERROR, "%s: prepare domain env err\n");
     } else {
          char *xml = file2str(conf_path);
          virDomainPtr domain;
          domain = create_transient_domain (
               DCH->sc->conn, xml);
          if ( domain == NULL )
               err = 1;
     }

     // TODO: wait the status of domain
     //sleep(10);

     // TODO: dynamic get status of domain
     if (!err)
     {
          DCH->dip->status = DOMAIN_S_RUNNING;
          strcpy(DCH->dip->ip, "preparing ...");
     }

     __tell_control_server(DCH->sc, LA_DOMAIN_STATUS,
                           sizeof(DomainInfo), DCH->dip);
}

static void __domain_stop (DomainControlHandler *DCH)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

     if (domain_stop (DCH->sc->conn, DCH->dip->name))
     {
          logprintfl(LYERROR, "%s: stop domain err\n",
                     __func__);
     } else {
          logprintfl(LYDEBUG, "%s: stop domain success\n",
                     __func__);
     }

     // TODO: wait the status of domain
     sleep(10);
     // TODO: dynamic get status of domain
     DCH->dip->status = DOMAIN_S_STOP;
     __tell_control_server(DCH->sc, LA_DOMAIN_STATUS,
                           sizeof(DomainInfo), DCH->dip);
}

static void __domain_suspend (DomainControlHandler *DCH)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

}

static void __domain_save (DomainControlHandler *DCH)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

}

static void __domain_reboot (DomainControlHandler *DCH)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

}

static int
__prepare_domain_env( DomainControlHandler *DCH,
                      char *conf_path )
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

     int sk, err;
     sk = connect_to_host(DCH->sc->cts_ip, DCH->sc->cts_port);
     if ( sk <= 0 ) return -1;
     
     err = __send_request(sk, LA_CP_GET_IMAGE_INFO,
                          sizeof(DCH->dip->diskimg),
                          &DCH->dip->diskimg);
     if (err)
     {
          close(sk);
          return -1;
     }

     LySockRespond respond;
     ImageInfo ii;
     err = __get_respond(sk, &respond,
                         sizeof(ImageInfo), &ii);
     if (err)
     {
          close(sk);
          return -2;
     }

     // download configure file
     sprintf(conf_path, "%s/%d/domain.conf",
             DCH->sc->root_path, DCH->dip->id);

     if ( !check_file(conf_path) )
          logprintfl(LYDEBUG, "%s exist\n", conf_path);
     else {
          char conf_url[LINE_MAX];
          sprintf(conf_url, "%s/%d/",
                  DCH->sc->root_path, DCH->dip->id);
          lyu_make_sure_dir_exist(conf_url);

          //sprintf( conf_url, "http://%s/domain/%d/conf/",
          //         DCH->sc->cts_ip, DCH->dip->id );
          sprintf( conf_url, "http://corei5/domain/%d/conf/",
                   DCH->dip->id );
          if ( 0 != ly_dl(conf_url, conf_path) )
               return -1;
     }

     char decompress_img_path[LINE_MAX];
     sprintf(decompress_img_path, "%s/%d/images/%d_%d_%s",
             DCH->sc->root_path, DCH->dip->id,
             ii.type, ii.id, ii.checksum_value);

     if ( !check_file(decompress_img_path) )
          logprintfl(LYDEBUG, "%s exist\n",
                     decompress_img_path);
     else {
          // TODO: should use compress type
          char compress_img_path[LINE_MAX];
          sprintf(compress_img_path, "%s.gz",
                  decompress_img_path);

          if ( !check_file(compress_img_path) )
               logprintfl(LYDEBUG, "%s exist\n",
                          compress_img_path);
          else {
               char img_url[LINE_MAX];
               sprintf( img_url, "%s/%d/images/",
                        DCH->sc->root_path, DCH->dip->id);
               lyu_make_sure_dir_exist(img_url);

               //sprintf( img_url, "http://%s/images/%d_%d_%s",
               //         DCH->sc->cts_ip, ii.type,
               //         ii.id, ii.checksum_value );
               sprintf( img_url, "http://corei5/images/%d_%d_%s",
                        ii.type, ii.id, ii.checksum_value );
               if (0 != ly_dl(img_url, compress_img_path))
                    return -2;
          }

          //if (0 != lyu_decompress_bzip2(compress_img_path,
          //                             decompress_img_path))
          if (0 != lyu_decompress_gz(compress_img_path,
                                     decompress_img_path))
          {
               logprintfl(LYDEBUG, "%s: decompress error\n",
                          __func__);
               return -3;
          }
     }

     // write the dynamic conf to disk img
     __write_conf_to_img(DCH, decompress_img_path);

     // TODO: auto create conf file by DomainInfo

     return 0;
}


/* Write the dynamic configure to img file */
static int
__write_conf_to_img (DomainControlHandler *DCH, 
                     char *img_path)
{
     unsigned long long offset;
     dk_set_boot_partition_offset(img_path, &offset);

     char *mount_path;
     // Fix me: tempnam is dangerous
     mount_path = tempnam("/tmp", "LuoYun_");
     if ( lyu_make_sure_dir_exist(mount_path) != 0 )
          return -1;

     // TODO: should not use system call !
     char cmd[1024];
     sprintf(cmd, "mount -o loop,offset=%lld %s %s",
             offset, img_path, mount_path);
     logprintfl(LYDEBUG, "system call: \"%s\"\n", cmd);
     printf("[DD] %s\n", cmd);
     system(cmd);

     sprintf(cmd, "%s/LuoYun/", mount_path);
     if ( lyu_make_sure_dir_exist(cmd) != 0 )
          return -1;

     FILE *fp;
     sprintf(cmd, "%s/LuoYun/LuoYun.conf", mount_path);
     fp = fopen(cmd, "w+");
     if (fp == NULL)
     {
          perror("open error");
     } else {
          fprintf(fp, "CONTROL_SERVER_IP = %s\n"
                  "CONTROL_SERVER_PORT = %d\n"
                  "DOMAIN_ID = %d\n"
                  "NODE_ID = %d\n",
                  DCH->sc->cts_ip, DCH->sc->cts_port,
                  DCH->dip->id, DCH->dip->node);
          fclose(fp);
     }

     sprintf(cmd, "umount %s", mount_path);
     logprintfl(LYDEBUG, "system call: \"%s\"\n", cmd);
     system(cmd);

     // TODO: make sure the mount_path have umount!

     // TODO: unlink the mount path

     free(mount_path);

     return 0;

}
