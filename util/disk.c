#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "util/misc.h"
#include "util/disk.h"


#define hex_val(c)      ({                      \
               char _c = (c);                   \
               isdigit(_c) ? _c - '0' :         \
                    tolower(_c) + 10 - 'a';     \
          })

#define LINE_LENGTH     800

#define pt_offset(b, n)                         \
     ((struct partition *)((b) + 0x1be +        \
                           (n) * sizeof(struct partition)))

#define sector(s)       ((s) & 0x3f)

#define cylinder(s, c)  ((c) | (((s) & 0xc0) << 2))

#define hsc2sector(h,s,c) (sector(s) - 1 + sectors *  \
                           ((h) + heads * cylinder(s,c)))

#define set_hsc(h,s,c,sector) {                 \
          s = sector % sectors + 1;             \
          sector /= sectors;                    \
          h = sector % heads;                   \
          sector /= heads;                      \
          c = sector & 0xff;                    \
          s |= (sector >> 2) & 0xc0;            \
     }


/* A valid partition table sector ends in 0x55 0xaa */
#if 0
static unsigned int
part_table_flag(unsigned char *b)
{
     return ((unsigned int) b[510])
          + (((unsigned int) b[511]) << 8);
}

int
valid_part_table_flag(unsigned char *b)
{
     return (b[510] == 0x55 && b[511] == 0xaa);
}

static void
write_part_table_flag(unsigned char *b)
{
     b[510] = 0x55;
     b[511] = 0xaa;
}

/* start_sect and nr_sects are stored little endian on all machines */
/* moreover, they are not aligned correctly */
static void
store4_little_endian (unsigned char *cp, unsigned int val)
{
     cp[0] = (val & 0xff);
     cp[1] = ((val >> 8) & 0xff);
     cp[2] = ((val >> 16) & 0xff);
     cp[3] = ((val >> 24) & 0xff);
}
#endif


static unsigned int
read4_little_endian (const unsigned char *cp)
{
     return (unsigned int)(cp[0])
          + ((unsigned int)(cp[1]) << 8)
          + ((unsigned int)(cp[2]) << 16)
          + ((unsigned int)(cp[3]) << 24);
}


unsigned long long
get_start_sect(struct partition *p)
{
     return read4_little_endian(p->start4);
}

unsigned long long
get_nr_sects(struct partition *p)
{
     return read4_little_endian(p->size4);
}


/* Read x bytes from fd */
#if 0
static ssize_t
xread(int fd, void *buf, size_t count)
{
     char *p = buf;
     ssize_t out = 0;
     ssize_t rv;

     while (count) {
          rv = read(fd, p, count);
          if (rv == -1) {
               if (errno == EINTR || errno == EAGAIN)
                    continue;
               return out ? out : -1; /* Error */
          } else if (rv == 0) {
               return out; /* EOF */
          }

          p += rv;
          out += rv;
          count -= rv;
     }

     return out;
}
#endif

int
dk_set_boot_partition_offset (const char *disk_device,
                              unsigned long long *offset)
{
     int fd;
     char MBRbuffer[1024];

     if ((fd = open(disk_device, O_RDONLY)) < 0) {
          logprintfl(LYERROR, "You will not be able to read "
                     "the partition table from %s.\n",
                     disk_device);
          return -1;
     }

     if (512 != read(fd, MBRbuffer, 512)) {
          logprintfl(LYERROR, "unable read from %s\n",
                     disk_device);
     }

     close(fd);

     int i;
     struct partition *p;
     for (i = 0; i < 4; i++)
     {
          p = pt_offset(MBRbuffer, i);

          if (p->boot_ind == 0x80)
          {
               *offset = get_start_sect(p) * 512;
               return 0;
          }

          if (p->boot_ind != 0 && p->boot_ind != 0x80)
          {
               logprintfl(LYDEBUG, "ERR boot flag: %x\n",
                    p->boot_ind);
          }

     }

     return -1;
}


int
dk_read_dpt(const char *disk_device)
{
     int fd;
     char MBRbuffer[1024];

     if ((fd = open(disk_device, O_RDONLY)) < 0) {
          logprintfl(LYERROR, "You will not be able to read "
                     "the partition table from %s.\n",
                     disk_device);
          return -1;
     }

     if (512 != read(fd, MBRbuffer, 512)) {
          logprintfl(LYERROR, "unable read from %s\n",
                     disk_device);
     }

     close(fd);

     int i;
     struct partition *p;
     for (i = 0; i < 4; i++)
     {
          p = pt_offset(MBRbuffer, i);
          if (p->boot_ind != 0 && p->boot_ind != 0x80)
          {
               logprintfl(LYDEBUG, "ERR boot flag: %d\n",
                    p->boot_ind);
          }
          logprintfl(LYDEBUG, "%d, boot_ind = %x, "
                     "start sect = %ld (%ld), "
                     "nr sect = %ld (%ld)\n",
                     i, p->boot_ind, get_start_sect(p),
                     get_start_sect(p) * 512,
                     get_nr_sects(p),
                     get_nr_sects(p) * 512);

     }

     return 0;
}




static int
__print_dpt_info (char dpt[])
{
     unsigned char state = 0;
     unsigned char begin_head = 0;
     unsigned int begin_sc = 0;
     unsigned char fsid = 0;
     unsigned char end_head = 0;
     unsigned int end_sc = 0;
     unsigned long start_sec = 0;
     unsigned long total_sec = 0;

     memcpy(&state, dpt + DPT_OFF_STATE, 1);
     memcpy(&begin_head, dpt + DPT_OFF_BEGINHEAD, 1);
     memcpy(&begin_sc, dpt + DPT_OFF_BEGINSC, 2);
     memcpy(&fsid, dpt + DPT_OFF_FSID, 1);
     memcpy(&end_head, dpt + DPT_OFF_ENDHEAD, 1);
     memcpy(&end_sc, dpt + DPT_OFF_ENDSC, 2);
     memcpy(&start_sec, dpt + DPT_OFF_STARTSEC, 4);
     memcpy(&total_sec, dpt + DPT_OFF_TOTALSEC, 4);

     // do begin_sc
     // do end_sc;

     logsimple("\nstate : %d\n"
               "begin_head : %d\n"
               "begin_sc : %d\n"
               "fsid : %d\n"
               "end_head : %d\n"
               "end_sc : %d\n"
               "start_sec : %ld ( * 512 = %ld )\n"
               "total_sec : %ld ( * 512 = %ld )\n",
               state, begin_head, begin_sc,
               fsid, end_head, end_sc,
               start_sec, start_sec * 512,
               total_sec, total_sec * 512);

     return 0;
}


int dk_print_dpt (char *file)
{
     FILE *fp;

     fp = fopen(file, "rb");
     if (fp == NULL)
     {
          logprintfl(LYDEBUG, "%s: open %s error\n",
                     __func__, file);
          return -1;
     }

     int i, rnum;
     char dpt[16];

     fseek(fp, 446, SEEK_SET);
     for (i = 0; i < 4; i++)
     {
          rnum = fread(dpt, 16, 1, fp);
          if (rnum != 1)
          {
               logprintfl(LYDEBUG, "%s: read dpt from \
%s error\n", __func__, file);
               fclose(fp);
               return -2;
          }
          
          __print_dpt_info(dpt);
     }

     fclose(fp);
     return 0;
}

