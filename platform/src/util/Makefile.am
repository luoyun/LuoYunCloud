
AM_CFLAGS = -g -O -std=gnu99 -D_GNU_SOURCE
AM_CPPFLAGS = -I/usr/include/libxml2

noinst_LIBRARIES = libutil.a
libutil_a_SOURCES = $(top_srcdir)/config.h list.h \
                    disk.c disk.h download.c download.h \
                    misc.c misc.h logging.c logging.h md5.c md5.h \
                    lyxml.c lyxml.h lyxml_data.c \
                    lypacket.c lypacket.h \
                    lyauth.c lyauth.h \
                    lyutil.c lyutil.h

noinst_PROGRAMS = test 
test_SOURCES = test.c 
test_LDADD = libutil.a 

CLEANFILES = *~
