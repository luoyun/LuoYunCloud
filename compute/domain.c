#include "compute/domain.h"


void __customErrorFunc(void *userdata, virErrorPtr err)
{
     logprintf("Failure of libvirt library call:\n");
     logsimple("  Code: %d\n", err->code);
     logsimple("  Domain: %d\n", err->domain);
     logsimple("  Message: %s\n", err->message);
     logsimple("  Level: %d\n", err->level);
     logsimple("  str1: %s\n", err->str1);
     logsimple("  str2: %s\n", err->str2);
     logsimple("  str3: %s\n", err->str3);
     logsimple("  int1: %d\n", err->int1);
     logsimple("  int2: %d\n", err->int2);
}


virConnectPtr
libvirtd_connect (LyComputeServerConfig *sc)
{

     if (sc->conn != NULL)
     {
          logprintfl(LYERROR, "conneted already.\n");
          return sc->conn;
     }

     virSetErrorFunc(NULL, __customErrorFunc);

     char *URI = "qemu:///system";
     sc->conn = virConnectOpen(URI);
     if (NULL == sc->conn)
     {
          logprintfl(LYERROR, "Connet to %s error.\n", URI);
          return NULL;
     }
     else
     {
          logprintfl(LYINFO, "Connect to %s success!\n", URI);
     }

     return sc->conn;
}



int
set_hypervisor (LyComputeServerConfig *sc)
{
     const char *type;
     type = virConnectGetType(sc->conn);
     if (NULL == type)
     {
          logprintfl(LYERROR, "virConnectGetType() error.\n");
          return -1;
     }

     if ( !strcmp("QEMU", type) )
          sc->node->hypervisor = HYPERVISOR_IS_KVM;

     //free(type);

     return 0;
}

int
set_hypervisor_version (LyComputeServerConfig *sc)
{

     if ( 0 != virConnectGetVersion(
               sc->conn, &(sc->node->hypervisor_version)) )
     {
          logprintfl(LYERROR, "virConnectGetVersion err\n");
          return -1;
     }

     return 0;
}


int
set_libversion (LyComputeServerConfig *sc)
{
     if ( 0 != virConnectGetLibVersion(
               sc->conn, &(sc->node->libversion)) )
     {
          logprintfl(LYERROR, "virConnectGetLibVersion err\n");
          return -1;
     }

     return 0;
}


/*
static int set_uri(Node *node)
{
     node->uri = virConnectGetURI(node->conn);
     if (NULL == node->uri)
     {
          logprintfl(SCERROR, "set_uri() error.\n");
          return -1;
     }

     return 0;
}
*/


int
set_hostname (LyComputeServerConfig *sc)
{
     strcpy(sc->node->hostname,
            virConnectGetHostname(sc->conn));
     if (NULL == sc->node->hostname)
     {
          logprintfl(LYERROR, "virConnectGetHostname err\n");
          return -1;
     }

     return 0;
}


int
set_max_cpus (LyComputeServerConfig *sc)
{
     sc->node->max_cpus = 
          virConnectGetMaxVcpus(sc->conn, NULL);
     if (-1 == sc->node->max_cpus)
     {
          logprintfl(LYERROR, "virConnectGetMaxVcpus err\n");
          return -1;
     }

     return 0;
}


int
set_node_mixture (LyComputeServerConfig *sc)
{
     virNodeInfo *nf;
     nf = malloc(sizeof(virNodeInfo));
     if (NULL == nf)
     {
          logprintfl(LYERROR, "virNodeInfo malloc err\n");
          return -1;
     }

     /* success = 0, failed = -1 */
     if ( 0 != virNodeGetInfo(sc->conn, nf) )
     {
          logprintfl(LYERROR, "virNodeGetInfo err\n");
          return -2;
     }

     strcpy(sc->node->cpu_model, nf->model);
     sc->node->max_memory = nf->memory;
     sc->node->max_cpus = nf->cpus;
     sc->node->cpu_mhz = nf->mhz;
     //sc->node->numaNodes = nf->nodes;
     //node->sockets = nf->sockets;
     //node->coresPerSocket = nf->cores;
     //node->threadsPerCore = nf->threads;

     free(nf);
     return 0;
}

int
set_free_memory (LyComputeServerConfig *sc)
{
     //TODO: used virNodeGetMemoryStats
     sc->node->free_memory = virNodeGetFreeMemory(sc->conn);
     return 0;
}


virDomainPtr
domain_connect (virConnectPtr conn, char *name)
{
     virDomainPtr domain;
     domain = virDomainLookupByName(conn, name);
     if ( NULL == domain )
     {
          logprintfl(LYERROR, "%s: connet domain by name "
                     "error, name = %s\n", __func__, name);
     }

     return domain;
}


virDomainPtr
create_transient_domain(virConnectPtr conn, char *xml)
{
     virDomainPtr domain;

     domain = virDomainCreateXML(conn, xml, 0);
     if ( NULL == domain )
     {
          logprintfl(LYERROR, "%s: run error.\n", __func__);
     }

     return domain;
}


int
domain_stop (virConnectPtr conn, char *name)
{
     virDomainPtr domain;
     domain = domain_connect(conn, name);
     if ( NULL == domain )
     {
          logprintfl(LYERROR, "%s: can not connect to "
                     "domian %s\n", __func__, name);
          return -1;
     }

     if ( 0 != virDomainShutdown(domain))
     {
          logprintfl(LYERROR, "%s: shutdown domain err.\n",
                     __func__);
          return -2;
     }

     return 0;
}

#if 0


static int set_isEncrypted(Node *node)
{
     node->isEncrypted = virConnectIsEncrypted(node->conn);
     if (-1 == node->isEncrypted)
     {
          logprintfl(SCERROR, "set_isEncrypted() error.\n");
          return -1;
     }

     return 0;
}


static int set_isSecure(Node *node)
{
     node->isSecure = virConnectIsSecure(node->conn);
     if (-1 == node->isSecure)
     {
          logprintfl(SCERROR, "set_isSecure() error.\n");
          return -1;
     }

     return 0;
}



virDomainPtr connect_domain_by_name(Node *node, char *name)
{
     virDomainPtr domain;
     domain = virDomainLookupByName(node->conn, name);
     if ( NULL == domain )
     {
          logprintfl(SCERROR, "connet domain by name error, name = %s\n", name);
     }

     return domain;
}


virDomainPtr connect_domain_by_id(Node *node, int id)
{
     virDomainPtr domain;
     domain = virDomainLookupByID(node->conn, id);
     if ( NULL == domain )
     {
          logprintfl(SCERROR, "connet domain by id error, id = %d\n", id);
     }

     return domain;
}


virDomainPtr connect_domain_by_UUID(Node *node, char *UUID)
{
     virDomainPtr domain;
     domain = virDomainLookupByUUIDString(node->conn, UUID);
     if ( NULL == domain )
     {
          logprintfl(SCERROR, "connet domain by UUID error, UUID = %s\n", UUID);
     }

     return domain;
}


int *id_list_of_active_domains(Node *node, int *num)
{
     int *ids = NULL;

     *num = virConnectNumOfDomains(node->conn);
     ids = malloc( sizeof(int) * (*num) );
     if ( NULL == ids )
          logprintfl(SCERROR, "malloc error.\n");
     else
          *num = virConnectListDomains(node->conn, ids, *num);

     return ids;
}


char **name_list_of_inactive_domains(Node *node, int *num)
{
     char **names = NULL;

     *num = virConnectNumOfDefinedDomains(node->conn);
     names = malloc( sizeof( char *) * (*num) );
     if ( NULL == names )
          logprintfl(SCERROR, "malloc error.\n");
     else
          *num = virConnectListDefinedDomains(
               node->conn, names, *num);

     return names;
}


int list_domains(NodePtr node)
{
     printf("List all domains:\n");
     int i, num, *ids = NULL;
     ids = id_list_of_active_domains(node, &num);
     for ( i = 0; i < num; i++ )
     {
          printf("   %d\n", ids[i]);
     }

     char **names = NULL;
     names = name_list_of_inactive_domains(node, &num);
     for ( i = 0; i < num; i++ )
     {
          printf("   %s\n", names[i]);
     }

     return 0;
}

char **list_domain_names(NodePtr node)
{
     char **names = NULL;
     int num_names;

     int i, *ids = NULL;
     int num_active, num_inactive;
     ids = id_list_of_active_domains(node, &num_active);

     char **inactive_names = NULL;
     inactive_names = name_list_of_inactive_domains(node, &num_inactive);

     num_names = num_active + num_inactive;
     names = malloc( sizeof(char *) * num_names + 1 );

     if ( NULL == names )
     {
          logprintfl(SCERROR, "list_domain_names(), malloc error.\n");
          return NULL;
     }

     if ( NULL != ids )
     {
          virDomainPtr domain;
          const char *name;
          for ( i = 0; i < num_active; i++ )
          {
               domain = connect_domain_by_id(node, ids[i]);
               name = virDomainGetName(domain);
               names[i] = malloc(strlen(name) + 1);
               strcpy(names[i], name);
               virDomainFree(domain);
          }
     }

     if ( NULL != inactive_names )
     {
          for ( i = num_active; i < num_names; i++ )
          {
               names[i] = inactive_names[i - num_active];
          }
     }

     //*(names + num_names) = NULL;
     *(names + i) = NULL;

     return names;
}


const char *domain_state_by_name(NodePtr node, char *name)
{
     virDomainPtr domain;
     domain = connect_domain_by_name(node, name);
     if ( NULL == domain ) return "notexist";

     virDomainInfo info;
     virDomainGetInfo(domain, &info);

     switch (info.state)
     {
     case VIR_DOMAIN_NOSTATE:
          return "no state";
     case VIR_DOMAIN_RUNNING:
          return "running";
     case VIR_DOMAIN_BLOCKED:
          return "blocked";
     case VIR_DOMAIN_PAUSED:
          return "paused";
     case VIR_DOMAIN_SHUTDOWN:
          return "shutdown";
     case VIR_DOMAIN_SHUTOFF:
          return "shutoff";
     case VIR_DOMAIN_CRASHED:
          return "crashed";
     default:
          return "unknown";
     }
}





int vir_domain_control_reboot(NodePtr node, char *name)
{
     virDomainPtr domain;
     domain = connect_domain_by_name(node, name);
     if ( NULL == domain )
     {
          logprintfl(SCERROR, "can not connect to domian: %s\n", name);
          return -1;
     }

     if ( 0 != virDomainReboot(domain, 0))
     {
          logprintfl(SCERROR, "reboot domain error.\n");
          return -2;
     }

     return 0;
}


int vir_domain_control_start(NodePtr node, char *name)
{
     virDomainPtr domain;
     domain = connect_domain_by_name(node, name);
     if ( NULL == domain )
     {
          logprintfl(SCERROR, "can not connect to domian: %s\n", name);
          return -1;
     }

     if ( 0 != virDomainCreate(domain))
     {
          logprintfl(SCERROR, "start domain error.\n");
          return -2;
     }

     return 0;
}


int vir_domain_control_save(NodePtr node, char *name, int idonweb)
{
     virDomainPtr domain;
     domain = connect_domain_by_name(node, name);
     if ( NULL == domain ) return -1;

     virDomainInfo info;

     if (virDomainGetInfo(dom, &info) < 0 )
     {
          logprintfl(SCERROR, "Cannot check guest state\n");
          return -3;
     }

     if (info.state == VIR_DOMAIN_SHUTOFF)
     {
          logprintfl(SCERROR, "Not saving guest that isn't running\n");
          return -4;
     }
     const char *filename = "";
     if (virDomainSave(dom, filename) < 0)
     {
          fprintf(stderr, "Unable to save guest to %s\n", filename);
     }

     fprintf(stdout, "Guest state saved to %s\n", filename);

     virConnectClose(conn);
     return 0;

}
#endif

