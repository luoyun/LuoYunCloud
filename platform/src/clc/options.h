#ifndef __LUOYUN_INCLUDE_control_option_H
#define __LUOYUN_INCLUDE_control_option_H

#include "util/luoyun.h"

/* control server config */
#include <libpq-fe.h>
typedef struct CtConfig_t {
     char host_ip[MAX_IP_LEN]; /* control server ip */
     int  host_port;


     char db_name[MAX_USERNAME_LEN];
     char db_username[MAX_USERNAME_LEN];
     char db_password[MAX_PASSWORD_LEN];

     int  port; /* New attr */

     char config[LINE_MAX]; /* Config file path */
     char log[LINE_MAX];    /* log file path */
     char verbose;
     char debug;
     char daemon;
} CtConfig;



int parse_opt(int argc, char *argv[], CtConfig *c);



#endif /* End __LUOYUN_INCLUDE_control_option_H */
