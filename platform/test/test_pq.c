#include <libpq-fe.h>

#include "logging.h"

PGconn *
db_connect ( const char *dbname,
             const char *username,
             const char *password)
{
     logdebug("START %s:%d:%s\n",
              __FILE__, __LINE__, __func__);
     PGconn *conn = NULL;
     char conninfo[256];

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

void db_close(PGconn * conn)
{
    PQfinish(conn);
}

int db_print_nodes(PGconn * conn)
{
     PGresult *res;
     int row, rec_count;

     char sql[1024];
     sprintf(sql, "SELECT id, ip, 3261, status from node");

     logdebug("%s: exec SQL = \"%s\"\n", __func__, sql);

     res = PQexec(conn, sql);
     if (PQresultStatus(res) != PGRES_TUPLES_OK) {
          logerror("SQL exec error: sql = \"%s\", error = \"%s\"\n", sql, PQerrorMessage(conn));
          return -1;
     }

     rec_count = PQntuples(res);


     /* id, ip, port, status
        0   1   2     3     */
     for (row = 0; row < rec_count; row++) {
          printf("%s %s %s %s\n", PQgetvalue(res, row, 0), 
                 PQgetvalue(res, row, 1), PQgetvalue(res, row, 2),
                 PQgetvalue(res, row, 3));

     }

     PQclear(res);
     return 0;
}

int main()
{
    PGconn * conn = db_connect("lyweb", "luoyun", "luoyun");
    if (conn) 
        printf("db connected\n");
    else
        printf("db not connected\n");
    db_print_nodes(conn);
    db_close(conn);
    return 0;
}

