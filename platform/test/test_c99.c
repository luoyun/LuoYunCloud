#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>

#include "util/luoyun.h"

void testc99(void)
{
    printf("testing c99 feature\n");
    for (int i=0;i<10;i++)
        printf("%d ", i);
    printf("\n");
    return;
}

int main(void)
{
    printf("Hello LuoYun!\n");
    testc99();
    return 0;
}
