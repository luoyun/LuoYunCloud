#include "control/postgres.h"
#include "util/luoyun.h"


PGconn *
db_connect ( const char *dbname,
             const char *username,
             const char *password)
{
     logdebug("START %s:%d:%s\n",
              __FILE__, __LINE__, __func__);
     PGconn *conn = NULL;
     char conninfo[LINE_MAX];

     sprintf(conninfo, "dbname=%s user=%s password=%s",
             dbname, username, password);

     logdebug("Connect DB use { %s }\n", conninfo);

     conn = PQconnectdb(conninfo);

     if (PQstatus(conn) == CONNECTION_BAD) {
          logprintfl(LYERROR, "unable to connect to the database: %s\n", PQerrorMessage(conn));
          return NULL;
     }

     return conn;
}


int
db_get_jobs (LyDBConn *db, JobQueue *qp)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

     PGresult *res;
     int row, rec_count;

     char sql[LINE_MAX];
     sprintf(sql, "SELECT id, status, \
extract(epoch FROM created), extract(epoch FROM created), \
target_type, target_id, action from job \
where status = %d or status = %d;",
             JOB_S_PREPARE, JOB_S_RUNNING);

     //logprintfl(LYDEBUG, "%s: SQL = %s\n", __func__, sql);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logprintfl(LYERROR, "%s: get jobs failed: %s\n",
                     __func__, PQerrorMessage(db->conn));
          return -1;
     }

     rec_count = PQntuples(res);

     //logprintfl(LYDEBUG, "found %d new jobs.\n", rec_count);

     int err = 0;
     int job_id, job_status, job_exist;
     Job *jp;
     /* id, status, created, started, 
        0,   1,       2,        3,   
        target_type, target_id, action
        4,           5          6         */
     for (row = 0; row < rec_count; row++) {

          job_id = atoi(PQgetvalue(res, row, 0));
          job_status = atoi(PQgetvalue(res, row, 1));
          job_exist = 0;

          logsimple("\t[ job %d , status = %d\n",
                    job_id, job_status);

          for (jp = qp->q_head; jp != NULL; jp = jp->j_next)
          {
               // Fix me, just id ?
               if ( jp->j_id == job_id &&
                    jp->j_status == job_status )
               {
                    job_exist = 1;
                    break;
               }
          }

          /* If job exist, continue */
          if (job_exist) continue;

          // Create new job
          Job *jp = malloc(sizeof(Job));
          if (jp == NULL)
          {
               logdebug("%s%d%s job malloc error.\n",
                        __FILE__, __LINE__, __func__);
               err = -2;
               break;
          }
          jp->j_id = job_id;
          jp->j_status = job_status;
          jp->j_created = atol(PQgetvalue(res, row, 2));
          jp->j_started = atol(PQgetvalue(res, row, 3));
          jp->j_target_type = atoi(PQgetvalue(res, row, 4));
          jp->j_target_id = atoi(PQgetvalue(res, row, 5));
          jp->j_action = atoi(PQgetvalue(res, row, 6));

          /* Append new job to queue */
          jp->j_next = NULL;
          jp->j_prev = qp->q_tail;
          if (qp->q_tail != NULL)
               qp->q_tail->j_next = jp;
          else
               qp->q_head = jp;
          qp->q_tail = jp;
          qp->q_count++; /* Maybe useful after */
     }

     PQclear(res);
     return err;
}


/* Summary: get all nodes from DB 
   Return: 0 is OK, others on error */
int
db_get_nodes (LyDBConn *db, ComputeNodeQueue *qp)
{
     //logdebug("START %s:%d:%s\n",
     //           __FILE__, __LINE__, __func__);
     PGresult *res;
     int row, rec_count;

     char sql[] = "SELECT id, hostname, ip, port, \
arch, status, hypervisor, network_type, max_memory, max_cpus, \
cpu_model, cpu_mhz, extract(epoch FROM updated) from node;";

     //logdebug("%s\n", sql);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logerror("select node failed: %s\n",
                   PQerrorMessage(db->conn));
          return 1;
     }

     rec_count = PQntuples(res);

     //logdebug("found %d nodes.\n", rec_count);

     /*
       id, hostname, ip, port, arch, status, hypervisor,
       0,  1,        2,  3,    4,    5,      6,
       network_type,
       7,
       max_memory, max_cpus, cpu_model, cpu_mhz, updated
       8,         9,       10,        11,      12
     */
     int node_exist;
     int err = 0;
     for (row = 0; row < rec_count; row++) {

          // TODO: if created was too old would be drop.

          ComputeNodeItem *np;

          // Does it exist ?
          node_exist = 0;
          for (np = qp->q_head; np != NULL; np = np->n_next)
          {
               if ( !strcmp( np->n_info->ip,
                             PQgetvalue(res, row, 2)) )
               {
                    node_exist = 1;
                    break;
               }
          }

          if ( node_exist )
          {
               if (np->n_id != atoi(PQgetvalue(res, row, 0)))
                    np->n_id = atoi(PQgetvalue(res, row, 0));
               continue;
          }

          // Create new node

          np = malloc(sizeof(ComputeNodeItem));
          if (np == NULL)
          {
               logerror("node: malloc error.\n");
               err = -1;
               break;
          }
          np->n_id = atoi(PQgetvalue(res, row, 0));

          ComputeNodeInfo *ninfo;
          ninfo = malloc(sizeof(ComputeNodeInfo));
          if (ninfo == NULL)
          {
               logerror("ninfo: malloc error.\n");
               err = -2;
               break;
          }
          // TODO: maybe use strncpy()
          strcpy(ninfo->hostname, PQgetvalue(res, row, 1));
          strcpy(ninfo->ip, PQgetvalue(res, row, 2));
          ninfo->port = atoi(PQgetvalue(res, row, 3));
          ninfo->arch = atoi(PQgetvalue(res, row, 4));
          ninfo->status = atoi(PQgetvalue(res, row, 5));
          ninfo->hypervisor = atoi(PQgetvalue(res, row, 6));
          ninfo->network_type = atoi(PQgetvalue(res, row, 7));
          ninfo->max_memory = atoi(PQgetvalue(res, row, 8));
          ninfo->max_cpus = atoi(PQgetvalue(res, row, 9));
          strcpy(ninfo->cpu_model, PQgetvalue(res, row, 10));
          ninfo->cpu_mhz = atoi(PQgetvalue(res, row, 11));
          ninfo->updated = atol(PQgetvalue(res, row, 12));

          // TODO: active_flag should have multitype value.
          ninfo->active_flag = 0;

          np->n_info = ninfo;

          // Add node to queue
          np->n_next = NULL;
          np->n_prev = qp->q_tail;
          if (qp->q_tail != NULL)
               qp->q_tail->n_next = np;
          else
               qp->q_head = np;
          qp->q_tail = np;

     }

     PQclear(res);
     return err;
}

#if 0
/* Summary: updated all information for node */
int
db_update_node (PGconn *conn, ComputeNodeItem *nitem)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);
     ComputeNodeInfo *ni = nitem->n_info;
     char sql[LINE_MAX];

     sprintf(sql,
"UPDATE node SET hostname = '%s', \
ip = '%s', port = %d, arch = %d, status = %d, \
hypervisor = %d, \
network_type = %d, max_memory = %lld, max_cpus = %d, \
cpu_model = '%s', load_average = %d, free_memory = %lld, \
updated = %ld::abstime::timestamp \
WHERE id = %d;",
          ni->hostname, ni->ip, ni->port, ni->arch,
          ni->status, ni->hypervisor,
          ni->network_type, ni->max_memory, ni->max_cpus,
          ni->cpu_model, ni->load_average, ni->free_memory,
          ni->updated, nitem->n_id);

     logprintfl(LYDEBUG, "SQL = { %s }\n", sql);

     int err = 0;
     PGresult *res;
     res = PQexec(conn, sql);

     if (PQresultStatus(res) != PGRES_COMMAND_OK) {
          logprintfl(LYERROR, "%s: update node failed: %s\n",
                     __func__, PQerrorMessage(conn));
          err = -1;
     } else {
          logprintfl(LYDEBUG, "update node success.\n");
     }

     PQclear(res);
     return err;
}
#endif

int
db_node_register (LyDBConn *db, ComputeNodeItem *nitem)
{
     ComputeNodeInfo *ni = nitem->n_info;

     logdebug("%s:%d:%s: register %s:%d\n",
              __FILE__, __LINE__, __func__,
              ni->ip, ni->port);

     char sql[LINE_MAX];
     PGresult *res;

     time(&ni->created);

     sprintf(sql, "INSERT INTO node ( \
hostname, ip, port, arch, status, hypervisor, \
network_type, \
max_memory, max_cpus, cpu_model, load_average, \
free_memory, created, updated, config ) VALUES ( \
'%s', '%s', %d, %d, %d, %d, \
%d, \
%lld, %d, '%s', %d, \
%lld, %ld::abstime::timestamp, %ld::abstime::timestamp, '' );",
          ni->hostname, ni->ip, ni->port, ni->arch,
          ni->status, ni->hypervisor,
          ni->network_type, ni->max_memory, ni->max_cpus,
          ni->cpu_model, ni->load_average, 
          ni->free_memory, ni->created, ni->updated);

     //logprintfl(LYDEBUG, "SQL = { %s }\n", sql);
     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     int err = 0;
     if (PQresultStatus(res) != PGRES_COMMAND_OK) {
          logprintfl(LYERROR, "register node failed: %s\n",
                     PQerrorMessage(db->conn));
          err = -1;
     }

     /* Update the nitem->n_id */
     sprintf(sql,
             "SELECT id from node where ip = '%s';",
             ni->ip);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logprintfl(LYERROR,
                     "%s: select node failed: %s\n",
                     __func__, PQerrorMessage(db->conn));
          err = -2;
     }

     if ( PQntuples(res) == 1 )
     {
          nitem->n_id = atoi(PQgetvalue(res, 0, 0));
     } else {
          logprintfl(LYERROR, "%s:%d:%s "
                     "one ip match more id in db\n",
                     __FILE__, __LINE__,  __func__);
          err = -3;
     }

     PQclear(res);
     return err;
}


/* Summary: update the status of node */
int
db_update_node_status (LyDBConn *db, ComputeNodeItem *nitem)
{
     //logsimple("START %s:%d:%s\n",
     //          __FILE__, __LINE__, __func__);

     char sql[LINE_MAX];
     PGresult *res;
     int err = 0;

     sprintf(sql, "UPDATE node SET free_memory = %lld, \
status = %d, updated = %ld::abstime::timestamp \
WHERE id = %d;",
             nitem->n_info->free_memory,
             nitem->n_info->status, 
             nitem->n_info->updated, nitem->n_id);

     //logprintfl(LYDEBUG, "SQL = { %s }\n", sql);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_COMMAND_OK) {
          logerror("%s: update node status failed: %s\n",
                   __func__, PQerrorMessage(db->conn));
          err = -1;
     } else {
          //logerror("%s: update node status success.\n",
          //         __func__);
          err = 0;
     }

     PQclear(res);
     return err;
}


/* Summary: update the status of job */
int
db_update_job_status (LyDBConn *db, Job *jp)
{
     //logsimple("START %s:%d:%s\n",
     //          __FILE__, __LINE__, __func__);

     char sql[LINE_MAX];
     PGresult *res;
     int err = 0;

     if (jp->j_ended > 0)
          sprintf(sql, "UPDATE job SET status = %d, \
started = %ld::abstime::timestamp, \
ended = %ld::abstime::timestamp \
WHERE id = %d;",
                  jp->j_status,
                  (long)jp->j_started, 
                  (long)jp->j_ended,
                  jp->j_id);
     else
          sprintf(sql, "UPDATE job SET status = %d, \
started = %ld::abstime::timestamp \
WHERE id = %d;",
                  jp->j_status,
                  (long)jp->j_started,
                  jp->j_id);
 
     //logprintfl(LYDEBUG, "SQL = { %s }\n", sql);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_COMMAND_OK) {
          logprintfl(LYERROR, "%s: update job status "
                     "failed: %s\n",
                     __func__, PQerrorMessage(db->conn));
          err = -1;
     }

     PQclear(res);
     return err;
}


/* Summary: check the status of domain in DB 
   Return: 0 on OK, others on error */
int
db_update_domains (LyDBConn *db, ComputeNodeQueue *qp)
{
     logdebug("%s:%d:%s check the status of all domains\n",
              __FILE__, __LINE__, __func__);

     DomainInfo *dip;
     dip = malloc( sizeof(DomainInfo) );
     if ( dip == NULL )
     {
          logerror("%s: malloc dip err.\n", __func__);
          return -1;
     }

     PGresult *res;
     int rec_count;
     char sql[LINE_MAX];

     sprintf(sql, "SELECT id, node_id, status, \
extract(epoch FROM updated) from domain where \
status = %d;", DOMAIN_S_RUNNING);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logerror("exec SQL error: %s\n",
                   PQerrorMessage(db->conn));
          PQclear(res);
          return -2;
     }

     rec_count = PQntuples(res);

     /*
       id, node_id, status, updated
       0   1        2       3
     */
     int err = 0, row;
     int domain_id, node_id;
     //int status;
     int find_node = 0;
     time_t now, updated;
     ComputeNodeItem *np;
     PGresult *update_res;
     time(&now);
     for (row = 0; row < rec_count; row++) {
          domain_id = atoi(PQgetvalue(res, row, 0));
          node_id = atoi(PQgetvalue(res, row, 1));
          //status = atoi(PQgetvalue(res, row, 2));
          updated = atol(PQgetvalue(res, row, 3));

          //logdebug("check domain %d: [ status = %d,"
          //         "node_id = %d, updated = %ld ]\n",
          //         domain_id, atoi(PQgetvalue(res, row, 2)),
          //         node_id, updated);

          // Find the node
          pthread_rwlock_wrlock(&qp->q_lock);
          for (np = qp->q_head; np != NULL; np = np->n_next)
          {
               if (np->n_info->status != NODE_S_RUNNING)
                    continue;

               if (np->n_id == node_id)
               {
                    find_node = 1;
                    break;
               }
          }
          pthread_rwlock_unlock(&qp->q_lock);

          // TODO: configure the interval time
          if ( find_node && (now - updated) < 360 )
               continue;

          sprintf(sql, "UPDATE domain SET ip = 'unset', \
status = %d, updated = %ld::abstime::timestamp \
WHERE id = %d;",
                  DOMAIN_S_UNKNOWN,
                  now, domain_id);

          logdebug("%s\n", sql);

          // Update the domain status in DB
          pthread_mutex_lock(&db->lock);
          update_res = PQexec(db->conn, sql);
          pthread_mutex_unlock(&db->lock);

          if (PQresultStatus(update_res) != PGRES_TUPLES_OK)
          {
               logerror("update status of domain %d was "
                        "failed: %s\n", domain_id,
                        PQerrorMessage(db->conn));
               err += 1;
          }
          PQclear(update_res);
     }

     PQclear(res);
     return 0;
}


/* Summary: get domain info from DB 
   Return: NULL is error, others on OK */
DomainInfo *
db_get_domain (LyDBConn *db, int id)
{
     logdebug("START %s:%d:%s\n",
              __FILE__, __LINE__, __func__);

     DomainInfo *dip;
     dip = malloc( sizeof(DomainInfo) );
     if ( dip == NULL )
     {
          logprintfl(LYERROR, "%s: malloc err.\n", __func__);
          return NULL;
     }

     PGresult *res;
     int rec_count;
     char sql[LINE_MAX];

     sprintf(sql, "SELECT status, name, node_id, \
image_id, cpus, memory, \
extract(epoch FROM created), extract(epoch FROM updated) \
from domain where id = %d;", id);

     logprintfl(LYDEBUG, "%s\n", sql);

     res = PQexec(db->conn, sql);

     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logprintfl(LYERROR, "get domain failed: %s\n",
                     PQerrorMessage(db->conn));
          PQclear(res);
          return NULL;
     }

     rec_count = PQntuples(res);
     if (rec_count != 1)
     {
          logprintfl(LYERROR, "%s: more domain found.\n",
                     __func__);
          PQclear(res);
          return NULL;
     }

     /*
       status, name, node_id, image_id,
       0       1     2        3
       cpus, memory, created, updated
       4     5       6        7
     */
     dip->status = atoi(PQgetvalue(res, 0, 0));
     dip->id = id;
     strcpy(dip->name, PQgetvalue(res, 0, 1));
     dip->node = atoi(PQgetvalue(res, 0, 2));
     dip->diskimg = atoi(PQgetvalue(res, 0, 3));
     dip->cpus = atoi(PQgetvalue(res, 0, 4));
     dip->memory = atol(PQgetvalue(res, 0, 5));
     dip->created = atol(PQgetvalue(res, 0, 6));
     dip->updated = atol(PQgetvalue(res, 0, 7));


     PQclear(res);
     return dip;
}


/* Summary: get job info from DB 
   Return: NULL is error, others on OK */
Job *
db_get_job (LyDBConn *db, JobQueue *qp, int id)
{
     logdebug("%s:%d:%s job id = %d\n",
              __FILE__, __LINE__, __func__, id);

     PGresult *res;
     char sql[LINE_MAX];

     sprintf(sql, "SELECT status, \
extract(epoch FROM created), extract(epoch FROM started), \
extract(epoch FROM ended), target_type, target_id, action \
from job where id = %d;", id);

     //logdebug("%s: SQL = %s\n", __func__, sql);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logerror("%s: get job %d failed: %s\n",
                   __func__, id, PQerrorMessage(db->conn));
          free(res);
          return NULL;
     }

     int rec_count;
     rec_count = PQntuples(res);
     if (rec_count != 1)
     {
          logprintfl(LYERROR, "%s: more job found.\n",
                     __func__);
          PQclear(res);
          return NULL;
     }

     int job_status, job_exist;
     Job *jp;

     /* status, created, started, ended,
        0       1        2        3
        target_type, target_id, action
        4,           5          6 */

     job_status = atoi(PQgetvalue(res, 0, 0));
     job_exist = 0;

     for (jp = qp->q_head; jp != NULL; jp = jp->j_next)
     {
          if ( jp->j_id == id &&
               jp->j_status == job_status )
          {
               job_exist = 1;
               break;
          }
     }

     /* If job exist, return the job */
     if (job_exist)
     {
          free(res);
          return jp;
     }

     // Create new job
     jp = malloc(sizeof(Job));
     if (jp == NULL)
     {
          logprintfl(LYERROR, "%s: job malloc error.\n",
                     __func__);
          return NULL;
     }

     jp->j_id = id;
     jp->j_status = job_status;
     jp->j_created = atol(PQgetvalue(res, 0, 1));
     jp->j_started = atol(PQgetvalue(res, 0, 2));
     jp->j_ended = atol(PQgetvalue(res, 0, 3));
     jp->j_target_type = atoi(PQgetvalue(res, 0, 4));
     jp->j_target_id = atoi(PQgetvalue(res, 0, 5));
     jp->j_action = atoi(PQgetvalue(res, 0, 6));

     /* Append new job to queue */
     jp->j_next = NULL;
     jp->j_prev = qp->q_tail;
     if (qp->q_tail != NULL)
          qp->q_tail->j_next = jp;
     else
          qp->q_head = jp;
     qp->q_tail = jp;
     qp->q_count++; /* Maybe useful after */

     PQclear(res);
     return jp;
}


/* Summary: update the status of domain */
int
db_update_domain_status (LyDBConn *db, DomainInfo *dip)
{
     //logdebug("%s: update status of domain %d\n",
     //         __func__, dip->id);

     char sql[LINE_MAX];

     sprintf(sql, "UPDATE domain SET \
node_id = %d, status = %d, ip = '%s', \
updated = %ld::abstime::timestamp WHERE id = %d;",
             dip->node, dip->status, dip->ip,
             dip->updated, dip->id);

     //logprintfl(LYDEBUG, "SQL = { %s }\n", sql);

     int err = 0;
     PGresult *res;

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_COMMAND_OK) {
          logerror("update status of domain %d failed: %s\n",
                   dip->id, PQerrorMessage(db->conn));
          err = -1;
     } else {
          logdebug("update status of domain %d success.\n",
                   dip->id);
          err = 0;
     }

     PQclear(res);
     return err;
}


/* Summary: get domain info from DB 
   Return: NULL is error, others on OK */
ImageInfo *
db_get_image (LyDBConn *db, int id)
{
     logsimple("START %s:%d:%s\n",
               __FILE__, __LINE__, __func__);

     ImageInfo *iip;
     iip = malloc( sizeof(ImageInfo) );
     if ( iip == NULL )
     {
          logprintfl(LYERROR, "%s: malloc err.\n", __func__);
          return NULL;
     }

     PGresult *res;
     int rec_count;
     char sql[LINE_MAX];

     sprintf(sql, "SELECT name, filetype, checksum_type, \
checksum_value, size, extract(epoch FROM created), \
extract(epoch FROM updated) from image where id = %d;", id);

     logprintfl(LYDEBUG, "%s\n", sql);

     pthread_mutex_lock(&db->lock);
     res = PQexec(db->conn, sql);
     pthread_mutex_unlock(&db->lock);

     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logprintfl(LYERROR, "get image failed: %s\n",
                     PQerrorMessage(db->conn));
          PQclear(res);
          return NULL;
     }

     rec_count = PQntuples(res);
     if (rec_count != 1)
     {
          logprintfl(LYERROR, "%s: more image found.\n",
                     __func__);
          PQclear(res);
          return NULL;
     }

     /* name, type, checksum_type, checksum_value,
        0     1     2              3
        size, created, updated
        4     5        6 */
     strcpy(iip->name, PQgetvalue(res, 0, 0));
     iip->type = atoi(PQgetvalue(res, 0, 1));
     iip->checksum_type = atoi(PQgetvalue(res, 0, 2));
     strcpy(iip->checksum_value, PQgetvalue(res, 0, 3));
     iip->size = atol(PQgetvalue(res, 0, 4));
     iip->created = atol(PQgetvalue(res, 0, 5));
     iip->updated = atol(PQgetvalue(res, 0, 6));

     iip->id = id;

     PQclear(res);
     return iip;
}
