#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <path_utils.h>
#include <collection_tools.h>
#include <ini_config.h>

void getconf(void)
{
    struct collection_item *ini_config = NULL;
    struct collection_item *error_set = NULL;
    struct collection_item *item;
    int error;
    error = config_from_file("lynode", "../conf/lynode.conf",
                             &ini_config, INI_STOP_ON_NONE, &error_set);
    if (error) {
        printf("Read configuration returned error: %d.", error);
        return;
    }
    else {
        col_print_collection(ini_config);
        col_print_collection(error_set);
    }
    error = get_config_item(NULL, "LYNODE_LOG_PATH", ini_config, &item);
    if (error) {
        printf("error get_config_item\n");
    }
    else {
        const char *s = get_const_string_config_value(item, &error);
        if (!error)
            printf("%s has value %s\n", "LYNODE_LOG", s);
        else {
            printf("get_const_string_config_value error\n");
        }
    }
    if (ini_config) {
        free_ini_config(ini_config);
    }
    if (error_set)
        free_ini_config_errors(error_set);

    return;
}

int main(void)
{
    printf("Test program!\n");
    getconf();
    return 0;
}
