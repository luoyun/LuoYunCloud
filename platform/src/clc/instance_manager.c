#include "control/instance_manager.h"
#include "control/postgres.h"


int instance_queue_init(LyInstanceQueue *qp)
{
     qp->head = NULL;
     qp->tail = NULL;

     if ( pthread_rwlock_init(&qp->lock, NULL) )
       return -1;
     else
       return 0;
}


int instance_register(LyDBConn *db, LyInstanceQueue *qp, LyInstance *ins)
{
     pthread_rwlock_wrlock(&qp->lock);

     LyInstance *np;
     int ret = -1;

     for (np = qp->head; np != NULL; np = np->next)
     {
          // TODO: DomainInfo is useful
          if ( !strcmp(np->di.ip, ins->di.ip) )
          {
               ins->next = np->next;
               ins->prev = np->prev;
               memcpy(np, ins, sizeof(LyInstance));
          }
     }

     ret = db_update_instance(db, &(ins->di));

     if (np == NULL)
          goto clean;

     // Append to queue
     ins->next = NULL;
     ins->prev = qp->tail;
     if (qp->tail != NULL)
          qp->tail->next = ins;
     else
          qp->head = ins;
     qp->tail = ins;

clean:
     pthread_rwlock_unlock(&qp->lock);
     return ret;
}



int instance_remove(LyDBConn *db, LyInstanceQueue *qp,  int sfd)
{
     pthread_rwlock_wrlock(&qp->lock);

     int ret = -1;
     LyInstance *np;

     for (np = qp->head; np != NULL; np = np->next)
     {
          if (np->sfd == sfd)
               break;
     }

     if (np == NULL)
          goto clean;

     np->di.status = DOMAIN_S_STOP;
     strncpy(np->di.ip, "0.0.0.0", sizeof(np->di.ip));
     ret = db_update_instance(db, &(np->di));

     // Remove from the queue
     // TODO: should be done in a common func
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



int get_instance_id_by_sfd(LyInstanceQueue *qp, int sfd)
{
     int id = -1;
     LyInstance *np;

     pthread_rwlock_wrlock(&qp->lock);

     for (np = qp->head; np != NULL; np = np->next)
     {
          if (np->sfd == sfd)
          {
               id = np->id;
               break;
          }
     }

     pthread_rwlock_unlock(&qp->lock);

     return id;
}



int print_instance_queue(LyInstanceQueue *qp)
{
     LyInstance *np;

     if (qp == NULL)
     {
          logdebug(_("Instance queue is empty.\n"));
          return 0;
     }

     if (pthread_rwlock_rdlock(&qp->lock) != 0)
     {
          logerror(_("Can not lock instance queue.\n"));
          return -1;
     }

     logsimple(_("Current Instance Queue:\n"));

     for (np = qp->head; np != NULL; np = np->next)
     {
          logsimple(_("  - Instance %d (%s), status = %d,"
                      " sfd = %d\n"),
                    np->id, np->di.ip,
                    np->di.status, np->sfd);
     }

     pthread_rwlock_unlock(&qp->lock);
     return 0;
}
