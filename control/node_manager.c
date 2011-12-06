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
          if (lnp->n_id == np->n_id)
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
          if (lnp->n_id == np->n_id)
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
          if (!np->n_id) /* = 0 */
          {
               db_node_register(db, np);
          } else if (np->n_info->active_flag) {
               // TODO: maybe update all info about node
               db_update_node_status(db, np);
          }
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}



/* if the status is NODE_S_RUNNING and time is out, 
   then change status to NODE_S_UNKNOWN */
int
node_timeout_check (ComputeNodeQueue *qp, int timeout)
{
     //logdebug("START %s:%d:%s\n",
     //         __FILE__, __LINE__, __func__);

     if ( timeout < 10 )
          timeout = 30;

     pthread_rwlock_wrlock(&qp->q_lock);

     ComputeNodeItem *nitem;
     time_t now;

     for ( nitem = qp->q_head;
           nitem != NULL;
           nitem = nitem->n_next )
     {
          now = time(&now);

          if ( (now - nitem->n_info->updated) < timeout )
               continue;

          if ( nitem->n_info->status == NODE_S_RUNNING )
          {
               logdebug("Node %d is timeout\n", nitem->n_id);
               nitem->n_info->status = NODE_S_UNKNOWN;
               nitem->n_info->updated = now;
               nitem->n_info->active_flag = 1;
               qp->q_pflag = 1;
          }
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}


int print_node_queue (ComputeNodeQueue *qp)
{
     ComputeNodeItem *np;

     if (qp == NULL)
     {
          logprintfl(LYDEBUG, "node queue is empty.\n");
          return 0;
     }

     if (pthread_rwlock_rdlock(&qp->q_lock) != 0)
     {
          logprintfl(LYERROR, "can not lock node queue.\n");
          return -1;
     }

     logsimple("Current node list:\n");

     for (np = qp->q_head; np != NULL; np = np->n_next)
     {
          logsimple("\t- "
                    "node %d is %s, "
                    "%s:%d, free memory: %lld\n",
                    np->n_id,
                    __node_status_string(np->n_info->status),
                    np->n_info->ip,
                    np->n_info->port,
                    np->n_info->free_memory);
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return 0;
}


int
node_update_or_register ( ComputeNodeQueue *qp,
                          ComputeNodeItem *nitem )
{
     pthread_rwlock_wrlock(&qp->q_lock);

     ComputeNodeItem *np;
     int node_exist = 0;
     int err = 0;

     for (np = qp->q_head; np != NULL; np = np->n_next)
     {
          if ( !strcmp(np->n_info->ip, nitem->n_info->ip) )
          {
               node_exist = 1;
               break;
          }
     }

     if (node_exist)
     {
          memcpy( np->n_info, nitem->n_info,
                  sizeof(ComputeNodeInfo) );
          free(nitem);
          // TODO: np->n_info->active_flag !
          if (np->n_info->active_flag)
          {
               // TODO: update the whole info
               qp->q_pflag = 1;
          }
     } else {
          if (nitem->n_id)
               nitem->n_id = 0;
          /* Append to queue */
          nitem->n_next = NULL;
          nitem->n_prev = qp->q_tail;
          if (qp->q_tail != NULL)
               qp->q_tail->n_next = nitem;
          else
               qp->q_head = nitem;
          qp->q_tail = nitem;

          qp->q_pflag = 1;
     }

     pthread_rwlock_unlock(&qp->q_lock);
     return err;
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
          if (np->n_info->status != NODE_S_RUNNING)
               continue;

          if (great_node == NULL)
               great_node = np;
          else if ( np->n_info->free_memory > 
                    great_node->n_info->free_memory )
               great_node = np;
     }

     pthread_rwlock_unlock(&qp->q_lock);

     return great_node;
}
