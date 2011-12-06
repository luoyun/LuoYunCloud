#ifndef __LY_INCLUDE_UTIL_DOWNLOAD_H
#define __LY_INCLUDE_UTIL_DOWNLOAD_H

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <curl/curl.h>
#include <curl/types.h>
#include <curl/easy.h>

#include "util/misc.h"

int ly_dl (const char *url, const char *file);

#endif
