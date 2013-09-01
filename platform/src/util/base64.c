#include <stdint.h>
#include <stdlib.h>

static char base64en_table[] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                                'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
                                'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                                'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
                                'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                                'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                                'w', 'x', 'y', 'z', '0', '1', '2', '3',
                                '4', '5', '6', '7', '8', '9', '+', '/'};
static int base64en_byte_pos[] = {0, 2, 1};
static char base64de_table[256] = {-1,};

char * base64_encode(const unsigned char * idata, size_t ilen, size_t * olen)
{
    int i,j;

    *olen = ((ilen + 2) / 3) * 4;

    char *odata = malloc(*olen);
    if (odata == NULL)
        return NULL;

    for (i = 0, j = 0; i < ilen;) {
        uint32_t a = i < ilen ? idata[i++] : 0;
        uint32_t b = i < ilen ? idata[i++] : 0;
        uint32_t c = i < ilen ? idata[i++] : 0;
        uint32_t triple = (a << 0x10) | (b << 0x08) | c;
        odata[j++] = base64en_table[(triple >> 18) & 0x3F];
        odata[j++] = base64en_table[(triple >> 12) & 0x3F];
        odata[j++] = base64en_table[(triple >> 6) & 0x3F];
        odata[j++] = base64en_table[triple & 0x3F];
    }

    for (i = 0; i < base64en_byte_pos[ilen % 3]; i++)
        odata[*olen - i - 1] = '=';

    return odata;
}

unsigned char * base64_decode(const unsigned char * idata, size_t ilen, size_t * olen)
{
    int i,j;

    if (base64de_table[0] == -1) {
        base64de_table[0] = 0;
        for (i = 0; i < sizeof(base64en_table); i++)
            base64de_table[(unsigned char) base64en_table[i]] = i;
        base64de_table['='] = 0;
    }

    int ilen4 = ilen;
    if (ilen4 % 4 != 0) {
        ilen4 = ilen4 & (~3);
        if (idata[ilen4] != '=')
            ilen4 += 4;
    }

    *olen = ilen4 / 4 * 3;
    if (idata[ilen - 1] == '=')
        (*olen)--;
    if (idata[ilen - 2] == '=')
        (*olen)--;

    unsigned char *odata= malloc(*olen+1);
    if (odata== NULL)
        return NULL;

    for (i = 0, j = 0; i < ilen4;) {
        uint32_t a = base64de_table[idata[i++]];
        uint32_t b = base64de_table[idata[i++]];
        uint32_t c = base64de_table[idata[i++]];
        uint32_t d = base64de_table[idata[i++]];
        uint32_t triple = (a << 18) | (b << 12) | (c << 6) | d;
        if (j < *olen)
            odata[j++] = (triple >> 16) & 0xFF;
        if (j < *olen)
            odata[j++] = (triple >> 8) & 0xFF;
        if (j < *olen) 
            odata[j++] = triple& 0xFF;
    }
    odata[*olen]='\0';

    return odata;
}
/*
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
  char *o;
  char *o1;
  char s[40960];
  FILE *fp=fopen(argv[1], "rb");
  size_t n=fread(s,1,4096,fp);
  fclose(fp);
  size_t n1;
  o=base64_decode(s,(size_t)strlen(s),(size_t *)&n1);
  o[n1]=0;
  printf("%s\n", o);
  o1=base64_encode(o,(size_t)strlen(o),(size_t *)&n1);
  free(o);
  printf("%s\n",o1);
  return 0;
}
*/
