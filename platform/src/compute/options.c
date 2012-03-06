#include <stdio.h>
#include <string.h>

#include "compute/options.h"
#include "compute/lynode.h"


#include <getopt.h>

#define GETOPT_HELP_OPTION_DECL                 \
     "help", no_argument, NULL, 'h'
#define GETOPT_VERSION_OPTION_DECL              \
     "version", no_argument, NULL, 'V'

// Flag set by '--verbose'
static int verbose_flag;

static struct option const long_opts[] = {
     {"verbose", no_argument,       &verbose_flag, 1},
     {"brief",   no_argument,       &verbose_flag, 0},

     {"debug", no_argument, NULL, 'd'},
     {"daemon", no_argument, NULL, 'D'},
     {"config", required_argument, NULL, 'c'},
     {"log", required_argument, NULL, 'l'},
     {GETOPT_HELP_OPTION_DECL},
     {GETOPT_VERSION_OPTION_DECL},
     {NULL, 0, NULL, 0}
};



int parse_opt(int argc, char *argv[], CpConfig *c)
{
     int ret=0, opt=0;
     const char * const short_options ="c:hdDl:V";

     while (1)
     {
          // getopt_long stores the option index here.
          int option_index = 0;

          opt = getopt_long(argc, argv, short_options, 
                          long_opts, &option_index);

          if (opt == -1)
               break;

          switch (opt)
          {

          case 0:
               c->verbose = 1;
               break;

          case 'c' :
               strcpy (c->config, optarg);
               break;

          case 'l' :
               strcpy (c->log, optarg);
               break;

          case 'h' :
               ret = -1;
               break;

          case 'd' :
               c->debug = 1;
               break;

          case 'D' :
               c->daemon = 1;
               break;

          case 'V' :
               ret = -1;
               printf (_("%s : Version %s\n"),
                       PROGRAM_NAME, PROGRAM_VERSION);
               break;

          default :
               ret = -2;
               break;
          }
     }

     if (optind < argc) {
          printf("non-option ARGV-elements: ");
          while (optind < argc)
               printf("%s ", argv[optind++]);
          printf("\n");
     }

     return ret;
}
