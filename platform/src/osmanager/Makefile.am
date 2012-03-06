EXTRA_DIST = Makefile.standalone

AM_CFLAGS = -g -O -std=gnu99 -D_GNU_SOURCE

AM_CPPFLAGS =  -I. -I$(top_srcdir)

bin_PROGRAMS = lyosm
lyosm_SOURCES = events.c  events.h \
                lyauth.c  lyauth.h \
                lypacket.c  lypacket.h \
                osmanager.c osmanager.h \
                osmmisc.c osmmisc.h \
                osmutil.c osmutil.h \
                osmlog.c osmlog.h \
                options.c options.h \
                lyosm.h
LIBS = 
lyosm_LDFLAGS = -lm -luuid -lgcrypt

CLEANFILES = *~

