#include "compute/node.h"

int
__empty_node(ComputeNodeInfo *node)
{
     node->status = NODE_S_UNKNOWN;
     *(node->hostname) = '\0';
     *(node->ip) = '\0';
     node->arch = CPU_ARCH_UNKNOWN;
     node->hypervisor = HYPERVISOR_IS_UNKNOWN;
     node->network_type = 0;
     node->max_memory = 0;
     node->max_cpus = 0;
     *(node->cpu_model) = '\0';
     node->cpu_mhz = 0;
     node->load_average = 0;
     node->free_memory = 0;

     //node->created
     //node->updated

     return 0;
}

unsigned long long __free_memory()
{
     //cat /proc/meminfo | grep MemFree | awk '{print $2}'

     FILE *fp;
     fp = fopen("/proc/meminfo", "r");
     if (fp == NULL)
     {
          logerror("Read /proc/meminfo error\n");
          return -1;
     }

     unsigned long long mem = 0;

     char line[LINE_MAX];
     char value[64];
     int i;
     char *kstr;
     char *vstr;

     while(1)
     {
          if (fgets(line, LINE_MAX, fp) == NULL)
               break;

          if (str_filter_white_space(line) != 0) continue;

          vstr = strstr(line, ":");
          if (vstr == NULL)
               continue;
          else
               vstr++;

          if ((kstr = strstr(line, "MemFree")) != NULL)
          {
               //printf("%s\n", vstr);
               for(i=0; ; i++)
               {
                    if (vstr[i] == 'k' || vstr[i] == '\0')
                         break;
                    value[i] = vstr[i];
               }
               value[i] = '\0';
               //printf("value = %s\n", value);
               mem = atol(value);
               break;
          }
     }

     fclose(fp);

     return mem;
}


int init_node_info(CpConfig *c)
{
     if (c->conn == NULL)
     {
          logprintfl(LYERROR, "must connect to libvirtd first.\n");
          return -1;
     }

     c->node = malloc( sizeof(ComputeNodeInfo) );
     if (NULL == c->node)
     {
          logprintfl(LYERROR, "node info malloc error.\n");
          return -2;
     }

     __empty_node(c->node);

     int ret = 0;
     ret += set_hypervisor(c);
     ret += set_hostname(c);
     //ret += set_max_cpus(c);
     ret += set_node_mixture(c);
     //ret += set_free_memory(c);
     c->node->free_memory = __free_memory();

     // use KB
     //if (c->node->free_memory)
     //     c->node->free_memory /= 1024;

     if ( 0 != ret )
     {
          logprintfl(LYERROR, "init_node() error.\n");
          return -2;
     }


     return 0;
}


int
node_dynamic_status (LyComputeServerConfig *sc)
{
     if (sc->conn == NULL || sc->node == NULL)
     {
          logprintfl(LYERROR, "%s: LyComputeServerConfig have not init\n", __func__);
          return -1;
     }

     // TODO: active_flag should have multitype value
     sc->node->active_flag = 1;

     int ret = 0;
     //ret += set_max_cpus(sc);
     //ret += set_free_memory(sc);
     sc->node->free_memory = __free_memory();

     // use KB
     //if (sc->node->free_memory)
     //     sc->node->free_memory /= 1024;

     if ( 0 != ret )
     {
          logprintfl(LYERROR, "init_node() error.\n");
          return -2;
     }

     return 0;
}


void
print_node_info (ComputeNodeInfo *N)
{
     logsimple(
          "node = {\n"
          "\tstatus = %d\n"
          "\thostname = %s\n"
          "\tip = %s\n"
          "\tport = %d\n"

          "\tarch = %d\n"
          "\thypervisor = %d\n"
          "\tnetwork_type = %d\n"

          "\tmax_memory = %d\n"
          "\tmax_cpus = %d\n"
          "\tcpu_model = %s\n"

          "\tcpu_mhz = %d\n"
          "\tload_average = %d\n"
          "\tfree_memory = %d\n"
          /*"\tcreated = %d\n"*/
          /*"\tupdated = %d\n"*/
          "}\n",
          N->status, N->hostname, N->ip, N->port,
          N->arch, N->hypervisor, N->network_type,
          N->max_memory, N->max_cpus, N->cpu_model,
          N->cpu_mhz, N->load_average, N->free_memory);
}
