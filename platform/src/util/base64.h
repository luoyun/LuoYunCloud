#ifndef __LY_INCLUDE_UTIL_BASE64_H
#define __LY_INCLUDE_UTIL_BASE64_H

char * base64_encode(const unsigned char * idata, size_t ilen, size_t * olen);
unsigned char * base64_decode(const unsigned char * idata, size_t ilen, size_t * olen);

#endif
