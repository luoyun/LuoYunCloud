
AM_CFLAGS = -g -O -std=gnu99 -D_GNU_SOURCE -DVERSION=\"$(VERSION)\" -DPACKAGE="\"$(PACKAGE)\"" 

AM_CPPFLAGS =  -I. \
               -I$(top_srcdir) \
               -I$(top_srcdir)/lib/ding-libs/path_utils \
               -I$(top_srcdir)/lib/ding-libs/refarray \
               -I$(top_srcdir)/lib/ding-libs/collection \
               -I$(top_srcdir)/lib/ding-libs/ini \
               -I/usr/include/libxml2 \
               -I$(shell pg_config --includedir)

LIBS = -lm -pthread -lbz2 -lz -lxml2 -lpq -luuid -lgcrypt
bin_PROGRAMS = lyclc
lyclc_SOURCES = $(top_srcdir)/config.h \
                lyclc.c  lyclc.h  options.c  options.h entity.c entity.h \
                events.c  events.h ev_node.c ev_osm.c \
                lyjob.c lyjob.h lyjob2.c \
                postgres.c postgres.h \
                node.c node.h mcast.c
lyclc_LDADD = ../luoyun/libluoyun.a ../util/libutil.a ../../lib/libding.a

CLEANFILES = *~

