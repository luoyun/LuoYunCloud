#ifndef __LUOYUN_INCLUDE_POSTGRES_H
#define __LUOYUN_INCLUDE_POSTGRES_H


#include "job_manager.h"
#include "lyclc.h"


/* connect to postgresql server */
PGconn * db_connect ( const char *dbname,
                      const char *username,
                      const char *password);


/* method about job */
int db_get_jobs2(LyDBConn *db, JobQueue *qp);

// old method
int db_get_jobs(LyDBConn *db, JobQueue *qp);
Job *db_get_job (LyDBConn *db, JobQueue *qp, int id);
int db_update_job_status (LyDBConn *db, Job *jp);


/* method about node */
int db_get_nodes(LyDBConn *db, ComputeNodeQueue *qp);
int db_update_node(LyDBConn *db, ComputeNodeItem *nitem);
int db_update_node_status(LyDBConn *db, ComputeNodeItem *nitem);
int db_node_register (LyDBConn *db, ComputeNodeItem *nitem);
int db_node_get_id(LyDBConn *db, const char *ip);


/* method about instance */
int db_update_instance(LyDBConn *db, DomainInfo *dip);


/* method about domain */
DomainInfo *db_get_domain (LyDBConn *db, int id);
int db_update_domain_status (LyDBConn *db, DomainInfo *dip);
int db_update_domains (LyDBConn *db, ComputeNodeQueue *qp);


/* method about image */
ImageInfo *db_get_image (LyDBConn *db, int id);





#endif /* End __LUOYUN_INCLUDE_POSTGRES_H */
