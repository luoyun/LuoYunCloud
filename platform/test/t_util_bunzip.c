#include <stdio.h>
#include "util/luoyun.h"


int main(int argc, char *argv[])
{
     if ( argc != 3 )
     {
          fprintf(stderr, "Usage: %s compress decompress \n",
                  argv[0]);
          return -1;
     }

     lyu_decompress_bzip2(argv[1], argv[2]);

     return 0;
}
