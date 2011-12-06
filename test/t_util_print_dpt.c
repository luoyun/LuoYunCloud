#include <stdio.h>
#include <stdlib.h>

#include "util/disk.h"

#include <sys/mount.h>

int main(int argc, char *argv[])
{
     if ( argc != 3 )
     {
          fprintf(stderr, "Usage: %s diskimg mountdir\n",
                  argv[0]);
          return -1;
     }

     //dk_print_dpt(argv[1]);
     dk_read_dpt(argv[1]);
     unsigned long long offset;
     dk_set_boot_partition_offset(argv[1], &offset);
     printf("==> boot partition offset: %lld\n", offset);

/*
int mount(const char *source, const char *target,
       const char *filesystemtype, unsigned long mountflags,
       const void *data);
*/
//mount( "/dev/hda/", "/", "fatfs" );
     char cmd[1024];
     sprintf(cmd, "mount -o loop,offset=%lld %s %s",
             offset, argv[1], argv[2]);
     printf("[DD] %s\n", cmd);
     system(cmd);

     sprintf(cmd, "%s/LuoYun.conf", argv[2]);
     FILE *fp;
     fp = fopen(cmd, "w+");
     if (fp == NULL)
     {
          perror("open error");
     } else {
          fprintf(fp, "Anther: test from LuoYun test program: %s\n",
                  argv[0]);
          fclose(fp);
     }

     sprintf(cmd, "umount %s", argv[2]);
     printf("[DD] %s\n", cmd);
     system(cmd);
     return 0;
}
