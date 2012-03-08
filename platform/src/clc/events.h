#ifndef __LY_INCLUDE_CLC_EVENTS_H
#define __LY_INCLUDE_CLC_EVENTS_H

#define EPOLL_EVENTS_MAX 64

extern int g_efd;

/* clc work socket receives connection */
int ly_epoll_entity_recv(int ent_id);

/* start clc main work socket */
int ly_epoll_work_start(int port);

/* events processing initialization */
int ly_epoll_init(unsigned int max_events);

/* stop and clean event processing */
int ly_epoll_close(void);

/*
** node packet handler 
**
** defined in ev_node.c
*/
int eh_process_node_xml(char * xml, int ent_id);
int eh_process_node_auth(int is_reply, void * data, int ent_id);

/*
** osmanager packet handler 
**
** defined in ev_osm.c
*/
int eh_process_osm_query(char *buf);
int eh_process_osm_register(char * buf, int size, int ent_id);
int eh_process_osm_report(char * buf, int size, int ent_id);
int eh_process_osm_auth(int is_reply, void * data, int ent_id);

#endif
