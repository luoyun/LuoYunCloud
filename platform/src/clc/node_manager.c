#include "node_manager.h"
#include "control/postgres.h"


static char *
__node_status_string(NodeStatus status)
{
     switch (status) {
     case NODE_S_RUNNING:
          return "RUNNING";
     case NODE_S_STOP:
          return "STOP";
     case NODE_S_UNKNOWN:
     default:
          return "UNKNOWN";
     }
}


int node_queue_init (ComputeNodeQueue *qp)
{
     int err;
     qp->q_head = NULL;
     qp->q_tail = NULL;
     qp->q_gflag = 1;
     qp->q_pflag = 0;
     err = pthread_rwlock_init(&qp->q_lock, NULL);
     if ( err != 0 ) return err;

     return 0;
}


int node_insert(ComputeNodeQueue *qp, ComputeNodeItem *np)
{
     pthread_rwlock_wrlock(&qp->q_lock);

     ComputeNodeItem *lnp;
     int node_exist = 0;

     for (lnp = qp->q_head; lnp != NULL; lnp = lnp->n_next)
     {
          if (lnp->id == np->id)
          {
               node_exist = 1;
               break;
          }
     }

     if (!node_exist)
     {
          np->n_next = qp->q_head;
          np->n_prev = NULL;
          if (qp->q_head != NULL)
               qp->q_head->n_prev = np;
          else
               qp->q_tail = np;

          qp->q_head = np;
     }

     pthread_rwlock_wrlock(&qp->q_lock);
     return 0;
}


int node_append (ComputeNodeQueue *qp, ComputeNodeItem *np)
{
     pthread_rwlock_wrlock(&qp->q_lock);

     ComputeNodeItem *lnp;
     int node_exist = 0;

     for (lnp = qp->q_head; lnp != NULL; lnp = lnp->n_next)
     {
          if (lnp->id == np->id)
          {
               node_exist = 1;
               break;
          }
     }

     if (!node_exist)
     {
          np->n_next = NULL;
          np->n_prev = qp->q_tail;
          if (qp->q_tail != NULL)
               qp->q_tail->n_next = np;
          else
               qp->q_head = np;
          qp->q_tail = np;
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}



int node_remove (ComputeNodeQueue *qp, ComputeNodeItem *np)
{
     pthread_rwlock_wrlock(&qp->q_lock);
     if (np == qp->q_head) {
          qp->q_head = np->n_next;
          if (qp->q_tail == np)
               qp->q_tail = NULL;
     } else if (np == qp->q_tail) {
          qp->q_tail = np->n_prev;
          if (qp->q_head == np)
               qp->q_head = NULL;
     } else {
          np->n_prev->n_next = np->n_next;
          np->n_next->n_prev = np->n_prev;
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}


/* DB -> ComputeNodeQueue */
int
get_node_queue (LyDBConn *db, ComputeNodeQueue *qp)
{
     logdebug("%s:%d:%s GET node queue from DB\n",
               __FILE__, __LINE__, __func__);

     pthread_rwlock_wrlock(&qp->q_lock);
     qp->q_gflag = 0;

     // TODO: g_db_mutex should be replace !
     db_get_nodes(db, qp);

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}

/* DB <- ComputeNodeQueue */
int
put_node_queue (LyDBConn *db, ComputeNodeQueue *qp)
{
     pthread_rwlock_wrlock(&qp->q_lock);
     qp->q_pflag = 0;

     ComputeNodeItem *np;

     for (np = qp->q_head; np != NULL; np = np->n_next)
     {
          db_update_node(db, np);
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}



int print_node_queue (ComputeNodeQueue *qp)
{
     ComputeNodeItem *np;

     if (qp == NULL)
     {
          logdebug(_("node queue is empty.\n"));
          return 0;
     }

     if (pthread_rwlock_rdlock(&qp->q_lock) != 0)
     {
          logerror(_("can not lock node queue.\n"));
          return -1;
     }

     logsimple(_("Current Node Queue:\n"));

     for (np = qp->q_head; np != NULL; np = np->n_next)
     {
          logsimple(_("  - NODE %d, %s:%d is %s, "
                      "free memory: %lld, socket fd: %d\n"),
                    np->id, np->node.ip, np->node.port,
                    __node_status_string(np->node.status),
                    np->node.free_memory, np->sfd);
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}



int node_register( LyDBConn *db,
                   ComputeNodeQueue *qp,
                   ComputeNodeItem *nitem )
{
     pthread_rwlock_wrlock(&qp->q_lock);

     ComputeNodeItem *np;
     int ret = 0;

     for (np = qp->q_head; np != NULL; np = np->n_next)
     {
          if ( !strcmp(np->node.ip, nitem->node.ip) )
          {
               // Update node
               nitem->n_next = np->n_next;
               nitem->n_prev = np->n_prev;
               nitem->id = np->id;
               memcpy(np, nitem, sizeof(ComputeNodeItem));

               ret = db_update_node(db, np);
               goto clean;
          }
     }

     // Register node
     ret = db_node_register(db, nitem);
     if (ret)
     {
          logerror(_("Register node to DB error.\n"));
          goto clean;
     }

     // Update node id
     if (!nitem->id)
     {
          nitem->id = db_node_get_id(db, nitem->node.ip);
          if (nitem->id <= 0)
          {
               //TODO:
          }
     }

     /* Append to queue */
     nitem->n_next = NULL;
     nitem->n_prev = qp->q_tail;
     if (qp->q_tail != NULL)
          qp->q_tail->n_next = nitem;
     else
          qp->q_head = nitem;
     qp->q_tail = nitem;


clean:
     pthread_rwlock_unlock(&qp->q_lock);
     return ret;
}



int node_remove2(LyDBConn *db, ComputeNodeQueue *qp,
                 int S /* socket fd */)
{
     pthread_rwlock_wrlock(&qp->q_lock);

     ComputeNodeItem *np;
     int ret = -1;

     for (np = qp->q_head; np != NULL; np = np->n_next)
     {
          if ( np->sfd == S )
          {
               np->node.status = NODE_S_STOP;
               ret = db_update_node(db, np);
               /* No need to care the return value */
               if (np == qp->q_head) {
                    qp->q_head = np->n_next;
                    if (qp->q_tail == np)
                         qp->q_tail = NULL;
               } else if (np == qp->q_tail) {
                    qp->q_tail = np->n_prev;
                    if (qp->q_head == np)
                         qp->q_head = NULL;
               } else {
                    np->n_prev->n_next = np->n_next;
                    np->n_next->n_prev = np->n_prev;
               }
               // TODO: should thread safe
               free(np); /* Import */
               break;
          }
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return ret;
}



/* Find node to run domain */
ComputeNodeItem *
find_node (ComputeNodeQueue *qp)
{
     ComputeNodeItem *np;
     ComputeNodeItem *great_node;

     pthread_rwlock_wrlock(&qp->q_lock);

     np = qp->q_head;
     great_node = NULL;

     for (; np != NULL; np = np->n_next)
     {
          if (np->node.status != NODE_S_RUNNING)
               continue;

          if (great_node == NULL)
               great_node = np;
          else if ( np->node.free_memory > 
                    great_node->node.free_memory )
               great_node = np;
     }

     pthread_rwlock_unlock(&qp->q_lock);

     return great_node;
}


int get_node_id_by_sfd(ComputeNodeQueue *qp, int sfd)
{
     int id = -1;
     ComputeNodeItem *np;

     pthread_rwlock_wrlock(&qp->q_lock);

     for (np = qp->q_head; np != NULL; np = np->n_next)
     {
          if (np->sfd == sfd)
          {
               id = np->id;
               break;
          }
     }

     pthread_rwlock_unlock(&qp->q_lock);

     return id;
}
