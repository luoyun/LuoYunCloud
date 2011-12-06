#include "util/download.h"


FILE *fp;


// CURLOPT_WRITEFUNCTION func
size_t write_data (void *ptr, size_t size, size_t nmemb, void *stream)
{
     int written = fwrite (ptr, size, nmemb, (FILE *) fp);
     return written;
}


int ly_dl (const char *url, const char *file)
{
     if ((fp = fopen (file, "w")) == NULL)
     {
          logprintfl(LYERROR, "can not open file: %s\n", file);
          return -1;
     }

     logprintfl(LYDEBUG, "download \"%s\" to \"%s\".\n", url, file);

     CURL *curl;

     curl_global_init (CURL_GLOBAL_ALL);
     curl = curl_easy_init ();
     curl_easy_setopt (curl, CURLOPT_URL, url);
     curl_easy_setopt (curl, CURLOPT_WRITEFUNCTION, write_data);
     curl_easy_perform (curl);
     curl_easy_cleanup (curl);

     fclose(fp); /* you should do this */

     return 0;
}
