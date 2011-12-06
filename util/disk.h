#ifndef __LUOYUN_INCLUDE_util_disk_H
#define __LUOYUN_INCLUDE_util_disk_H


typedef enum LyDPTOffset_t {
     DPT_OFF_STATE = 0,
     DPT_OFF_BEGINHEAD = 1,
     DPT_OFF_BEGINSC = 2,
     DPT_OFF_FSID = 3,
     DPT_OFF_ENDHEAD = 5,
     DPT_OFF_ENDSC = 6,
     DPT_OFF_STARTSEC = 8,
     DPT_OFF_TOTALSEC = 12,
} LyDPTOffset;


/* Ref util-linux/fdisk/fdisk.h */
#define DEFAULT_SECTOR_SIZE     512


struct partition {
     unsigned char boot_ind;     /* 0x80 - active */
     unsigned char head;         /* starting head */
     unsigned char sector;       /* starting sector */
     unsigned char cyl;          /* starting cylinder */
     unsigned char sys_ind;      /* What partition type */
     unsigned char end_head;     /* end head */
     unsigned char end_sector;   /* end sector */
     unsigned char end_cyl;      /* end cylinder */
     unsigned char start4[4];    /* starting sector counting from 0 */
     unsigned char size4[4];     /* nr of sectors in partition */
} PACKED;

enum failure {
     ioctl_error,
     unable_to_open, unable_to_read, unable_to_seek,
     unable_to_write
};

#define MAXIMUM_PARTS  5

struct pte {
     struct partition *part_table;   /* points into sectorbuffer */
     struct partition *ext_pointer;  /* points into sectorbuffer */
     char changed;                   /* boolean */
     unsigned long long offset;      /* disk sector number */
     unsigned char *sectorbuffer;    /* disk sector contents */
} ptes[MAXIMUM_PARTS];


int dk_set_boot_partition_offset (
     const char *disk_device,
     unsigned long long *offset );

int dk_read_dpt(const char *disk_device);


int dk_print_dpt (char *file);

#endif /* End __LUOYUN_INCLUDE_util_disk_H */
