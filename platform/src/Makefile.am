# Copyright (C) 2012 LuoYun Co. <admin@luoyun.co>
#  
# This file is free software; as a special exception the author gives
# unlimited permission to copy and/or distribute it, with or without 
# modifications, as long as this notice is preserved.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, to the extent permitted by law; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

SUBDIRS = luoyun util compute clc osmanager

AM_CFLAGS = -g -O -std=gnu99 -D_GNU_SOURCE -DVERSION=\"$(VERSION)\" -DPROG="\"$(PACKAGE)\""

AM_CPPFLAGS = -I$(top_srcdir) -I$(top_srcdir)/src/util \
              -I$(top_srcdir)/lib/ding-libs/path_utils \
              -I$(top_srcdir)/lib/ding-libs/refarray \
              -I$(top_srcdir)/lib/ding-libs/collection \
              -I$(top_srcdir)/lib/ding-libs/ini
CLEANFILES = *~

