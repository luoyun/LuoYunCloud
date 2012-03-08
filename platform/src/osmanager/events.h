#ifndef __LY_INCLUDE_OSMANAGER_EVENTS_H
#define __LY_INCLUDE_OSMANAGER_EVENTS_H

#include <sys/epoll.h>
/* in RHEL5, EPOLLRDHUP is not defined */
#ifndef EPOLLRDHUP
#define EPOLLRDHUP 0x2000
#endif

#define MAX_EVENTS 10

/* events processing initialization, init g_c->efd */
int ly_epoll_init(unsigned int max_events);
/* stop and clean event processing */
int ly_epoll_close(void);

/* work socket events registration, init g_c->wfd */
int ly_epoll_work_register(void);
/* work socket EPOLLIN event processing */
int ly_epoll_work_recv(void);
/* close work socket */
int ly_epoll_work_close(void);
/* macro for detecting work data-in event */
#define LY_EVENT_WORK_DATAIN(ev) ((ev.events & EPOLLIN) && (ev.data.fd == g_c->wfd))

/* mcast socket events registration, init g_c->mfd */
int ly_epoll_mcast_register(void);
/* mcast socket EPOLLIN event processing */
int ly_epoll_mcast_recv(void);
/* close mcast socket */
int ly_epoll_mcast_close(void);
/* macro for detecting mcast data-in event */
#define LY_EVENT_MCAST_DATAIN(ev) ((ev.events & EPOLLIN) && (ev.data.fd == g_c->mfd))

/* send register requst to clc */
int ly_osm_register(void);
int ly_osm_report(int status);

#endif
