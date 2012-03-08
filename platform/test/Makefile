##
## Copyright (C) 2012 LuoYun Co. 
##
##           Authors:
##                    lijian.gnu@gmail.com 
##                    zengdongwu@hotmail.com
##  
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##  
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##  
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##  
##

top_srcdir = ..

CC = gcc
CPPFLAGS := -I$(top_srcdir)\
            -I$(top_srcdir)/src \
            -I$(top_srcdir)/src/luoyun \
            -I$(top_srcdir)/src/util \
            -I$(top_srcdir)/src/compute \
            -I$(top_srcdir)/lib/ding-libs/path_utils \
            -I$(top_srcdir)/lib/ding-libs/refarray \
            -I$(top_srcdir)/lib/ding-libs/collection \
            -I$(top_srcdir)/lib/ding-libs/ini \
            -I/usr/include/libxml2
CFLAGS = -Wall -g -std=gnu99 -D_GNU_SOURCE -DVERSION=\"$(VERSION)\" -DPACKAGE="\"$(PACKAGE)\""
LDFLAGS = -lm -pthread -lvirt -lcurl -lbz2 -lz -lxml2 -lpq -luuid -lgcrypt
LDLIBS = ../src/luoyun/libluoyun.a ../src/util/libutil.a ../lib/libding.a
HEADERS = $(wildcard ../src/util/*.h)

RM = /bin/rm -f

TEST_PROG = test_list test_lydl test_pidfile test_socket\
            test_getconf test_getfreemem test_getmem \
            test_vm test_xml test_md5 test_lynode test_pq \
            test_misc test_crypt test_echo test_clc \
            test_nodeenable test_lyosm test_fileno
TEST_OBJ = $(addsuffix .o, $(TEST_PROG))

.PHONY : build clean

build : $(TEST_PROG)

#
# use make -pf/dev/null to see all the implicit rules
#
$(TEST_OBJ) :  $(HEADERS) Makefile

$(TEST_PROG) : $(LDLIBS)

test_vm.o : test_vm.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

test_vm : test_vm.o ../src/compute/domain.o ../src/compute/options.o ../src/compute/node.o ../src/compute/handler.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS)

clean :
	@$(RM) *.o *~ $(TEST_PROG)
