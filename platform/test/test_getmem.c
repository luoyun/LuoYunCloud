#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/sysinfo.h>

void getmem(void)
{
    int pagesize = getpagesize();
    int physpages = sysconf(_SC_PHYS_PAGES);
    int avphyspages = sysconf(_SC_AVPHYS_PAGES);
    int physpages_gnu = get_phys_pages();
    int avphyspages_gnu = get_avphys_pages();

    printf("page size:%d\n", pagesize);
    printf("total/available pages from sysconf, %d(%dKB) %d(%dKB)\n",
           physpages, physpages * (pagesize / 1024),
           avphyspages, avphyspages * (pagesize / 1024));
    printf("total/available pages from gnu extension, %d %d\n",
           physpages_gnu, avphyspages_gnu);
    return;
}

int main(void)
{
    printf("Test program!\n");
    getmem();
    return 0;
}
