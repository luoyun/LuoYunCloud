#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/sysinfo.h>

void usefscanf(void)
{
    long i, free = -1, buffers = -1, cached = -1;
    char s[41];
    FILE *fp = NULL;
    fp = fopen("/proc/meminfo", "r");
    if (fp == NULL) {
        printf("Can't open /proc/meminfo\n");
        printf("test failed\n");
        return;
    }
    while (fscanf(fp, "%40s %ld kB\n", s, &i) != EOF) {
        // printf("%s %ld\n", s, i);
        if (strncmp("MemFree:", s, 40) == 0)
            free = i;
        else if (strncmp("Buffers:", s, 40) == 0)
            buffers = i;
        else if (strncmp("Cached:", s, 40) == 0)
            cached = i;
        if (free != -1 && buffers != -1 && cached != -1)
            break;
    }
    if (free == -1 || buffers == -1 || cached == -1) {
        printf("Failed finding required fields %ld %ld %ld\n", free,
               buffers, cached);
        printf("test failed\n");
        return;
    }
    printf("total free memory: %ld\n", free + buffers + cached);
    fclose(fp);
    return;
}

int main(void)
{
    printf("Test program!\n");
    usefscanf();
    return 0;
}
