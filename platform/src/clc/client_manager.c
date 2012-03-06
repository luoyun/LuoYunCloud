#include "control/client_manager.h"
#include "control/postgres.h"


int client_queue_init(LyClientQueue *qp)
{
     qp->head = NULL;
     qp->tail = NULL;

     if ( pthread_rwlock_init(&qp->lock, NULL) )
       return -1;
     else
       return 0;
}


int client_register(LyClientQueue *qp, int id, int type, int sfd)
{
     LyClient *client;
     client = calloc(1, sizeof(LyClient));
     if ( client == NULL )
     {
          logerror(_("Allocate memory for LyClient failed.\n"));
          return -1;
     }

     client->id = id;
     client->type = type;
     client->sfd = sfd;

     pthread_rwlock_wrlock(&qp->lock);

     LyClient *np;

     for (np = qp->head; np != NULL; np = np->next)
     {
          if (np->sfd == client->sfd)
          {
               logdebug(_("Client(%d) exist already.\n"), client->sfd);
               free(client);
               goto clean;
          }
     }


     // Append client to the queue
     client->next = NULL;
     client->prev = qp->tail;
     if (qp->tail != NULL)
          qp->tail->next = client;
     else
          qp->head = client;
     qp->tail = client;

clean:
     pthread_rwlock_unlock(&qp->lock);
     return 0;
}


int client_remove(LyClientQueue *qp, LyDBConn *db, int sfd)
{
     pthread_rwlock_wrlock(&qp->lock);

     int ret = -1;
     LyClient *np;

     for (np = qp->head; np != NULL; np = np->next)
     {
          if (np->sfd == sfd)
               break;
     }

     if (np == NULL)
          goto clean;

     if (np->type == LY_CLIENT_IS_NODE) {
          logdebug(_("Client is node %d\n"), np->id);

     } else if (np->type == LY_CLIENT_IS_INSTANCE) {
          logdebug(_("Client is domain %d\n"), np->id);

          DomainInfo di;
          di.status = DOMAIN_S_STOP;
          di.id = np->id;
          ret = db_update_instance(db, &di);

     } else {
          logerror(_("Unknown type(%d) of client(%d).\n"), np->type, np->sfd);
          goto clean;
     }

     // Remove client from the queue
     if (np == qp->head) {
          qp->head = np->next;
          // np->next->prev = NULL; ???
          if (qp->tail == np)
               qp->tail = NULL;
     } else if (np == qp->tail) {
          qp->tail = np->prev;
          // np->prev->next = NULL; ???
          if (qp->head == np)
               qp->head = NULL;
     } else {
          np->prev->next = np->next;
          np->next->prev = np->prev;
     }

     free(np);
     ret = 0;

clean:
     pthread_rwlock_unlock(&qp->lock);
     return ret;
}
