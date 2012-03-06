/*
** Copyright (C) 2012 LuoYun Co. 
**
**           Authors:
**                    lijian.gnu@gmail.com 
**                    zengdongwu@hotmail.com
**  
** This program is free software; you can redistribute it and/or modify
** it under the terms of the GNU General Public License as published by
** the Free Software Foundation; either version 2 of the License, or
** (at your option) any later version.
**  
** This program is distributed in the hope that it will be useful,
** but WITHOUT ANY WARRANTY; without even the implied warranty of
** MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
** GNU General Public License for more details.
**  
** You should have received a copy of the GNU General Public License
** along with this program; if not, write to the Free Software
** Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
**  
*/
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <curl/curl.h>
#include <curl/easy.h>

#include "logging.h"
#include "download.h"

static size_t write_data(void *ptr, size_t size, size_t nmemb,
                         void *stream)
{
    int written = fwrite(ptr, size, nmemb, (FILE *) stream);
    return written;
}

/*
** This function is not thread-safe, protection required
*/
int lyutil_download(const char *url, const char *file)
{
    FILE *fp;
    int res = -1;

    if ((fp = fopen(file, "w")) == NULL) {
        logerror("Can not open file: %s\n", file);
        return -1;
    }

    logdebug("Download \"%s\" => \"%s\"\n", url, file);

    CURL *curl;

    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
        if (curl_easy_perform(curl) == CURLE_OK)
            res = 0;
        else {
            logerror("Failed downloading %s to %s\n", url, file);
            remove(file);
        }
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();

    fclose(fp);                 /* you should do this */

    return res;
}

