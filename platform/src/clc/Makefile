SC_SRC_DIR := $(if $(SC_SRC_DIR),$(SC_SRC_DIR),../)

CC = gcc
CFLAGS = -Wall -g -std=c99 -D_GNU_SOURCE
LDFLAGS = -lm -pthread -lpq -lbz2 -lz

INCLUDES := -I $(SC_SRC_DIR) -I$(shell pg_config --includedir)

RM = /bin/rm -f

# FILE_BN : file basename
FILE_BN = lyclc postgres job_manager node_manager handler options instance_manager
OBJ = $(addsuffix .o, $(FILE_BN))


.PHONY : all build clean


all : build


%.o : %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

#dependencies: $(OBJ:.o=.c)
#	$(CC) -M $^ > $@

#include dependencies


build : $(OBJ)
	$(CC) $(LDFLAGS) -o lyclc lyclc.o \
../util/misc.o ../util/luoyun.o postgres.o job_manager.o \
node_manager.o handler.o options.o instance_manager.o


test : build


clean :
	@$(RM) *.o lyclc cscope.out *.log
