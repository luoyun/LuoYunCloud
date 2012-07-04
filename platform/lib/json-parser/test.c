#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include "./json.h"

void myenum(json_value * data, int level)
{
    int i;
    for (int j=0; j<level; j++)
        printf("    ");
    switch (data->type) {
        case json_object:
            for (i = 0; i < data->u.object.length; i++) {
                printf("%s\n", data->u.object.values[i].name);
                myenum(data->u.object.values[i].value, level+1);
                for (int j=0; j<level; j++)
                    printf("    ");
            }
            break;
        case json_array:
            for (i = 0; i < data->u.array.length; i++) {
                printf("**ARRAY %d**\n",i);
                myenum(data->u.array.values[i], level+1);
                for (int j=0; j<level; j++)
                    printf("    ");
            }
            break;
        case json_integer:
            printf("%ld ", data->u.integer);
            break;
        case json_double:
            printf("%f ", data->u.dbl);
            break;
        case json_string:
            printf("%s(%d) ", data->u.string.ptr, data->u.string.length);
            break;
        case json_boolean:
            printf("%s ", data->u.boolean?"trun":"false");
            break;
        default:
            printf("***unknown*** ");
            break;
    }
    printf("\n");
}


int main(int argc, char **argv)
{
  char data[4096];

  if (argc != 2) {
    printf("wrong argument, json file is expected\n");
    return(1);
  }
  int fd = open(argv[1], O_RDONLY);
  int len;
  if (fd && (len = read(fd, data, 4096)) > 0) {
    if (len >= 4096) {
        printf("%s is too long\n", argv[1]);
        return(1);
    }
    // printf("%s\n", data);
    data[len] = '\0';
    json_settings settings;
    memset((void *)&settings, 0, sizeof (json_settings));
    char error[256];
    json_value * value = json_parse_ex(&settings, data, error);
    if (value == 0) {
      printf("json_parse error: %s\n", error);
      return(0);
    }
    myenum(value, 0);
    close(fd);
  }
  else {
    printf("open/read %s error\n", argv[1]);
    return(1);
  }

  return(0);
}
