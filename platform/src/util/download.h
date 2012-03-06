#ifndef __LY_INCLUDE_UTIL_DOWNLOAD_H
#define __LY_INCLUDE_UTIL_DOWNLOAD_H

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <curl/curl.h>
/* #include <curl/types.h> */
#include <curl/easy.h>

#include "misc.h"

/*
** download file,
** function is not thread-safe
*/
int lyutil_download(const char *uri, const char *name);

#endif
