SC_SRC_DIR := $(if $(SC_SRC_DIR),$(SC_SRC_DIR),../)

CC = gcc
CFLAGS = -Wall -g -std=c99 -D_GNU_SOURCE
LDFLAGS = -lm -pthread -lpq -lbz2 -lz

INCLUDES := -I $(SC_SRC_DIR) -I$(shell pg_config --includedir)

RM = /bin/rm -f

# FILE_BN : file basename
FILE_BN = server postgres job_manager node_manager handler
OBJ = $(addsuffix .o, $(FILE_BN))


.PHONY : all build clean


all : build


%.o : %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

#dependencies: $(OBJ:.o=.c)
#	$(CC) -M $^ > $@

#include dependencies


build : $(OBJ)
	$(CC) $(LDFLAGS) -o control_server server.o \
../util/misc.o ../util/luoyun.o postgres.o job_manager.o \
node_manager.o handler.o


test : build


clean :
	@$(RM) *.o control_server cscope.out *.log
