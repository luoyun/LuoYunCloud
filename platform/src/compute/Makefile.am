
AM_CFLAGS = -g -O -std=gnu99 -D_GNU_SOURCE -DVERSION=\"$(VERSION)\" -DPACKAGE="\"$(PACKAGE)\"" 

AM_CPPFLAGS =  -I. \
               -I$(top_srcdir) \
               -I$(top_srcdir)/lib/ding-libs/path_utils \
               -I$(top_srcdir)/lib/ding-libs/refarray \
               -I$(top_srcdir)/lib/ding-libs/collection \
               -I$(top_srcdir)/lib/ding-libs/ini \
               -I/usr/include/libxml2
LIBS =
bin_PROGRAMS = lynode
lynode_SOURCES = $(top_srcdir)/config.h \
                 domain.c  domain.h  handler.c  handler.h  lynode.c  lynode.h \
                 node.c  node.h  options.c  options.h events.c  events.h
lynode_LDADD = ../luoyun/libluoyun.a ../util/libutil.a ../../lib/libding.a
lynode_LDFLAGS = -lm -pthread -lvirt -lcurl -lbz2 -lz -lxml2 -luuid -lgcrypt

CLEANFILES = *~

