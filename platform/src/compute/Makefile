SC_SRC_DIR := $(if $(SC_SRC_DIR),$(SC_SRC_DIR),../)

CC = gcc
CFLAGS = -Wall -g -std=c99 -D_GNU_SOURCE
LDFLAGS = -lm -pthread -lvirt -lcurl -lbz2 -lz

INCLUDES := -I $(SC_SRC_DIR) -I$(shell pg_config --includedir)

RM = /bin/rm -f

# FILE_BN : file basename
FILE_BN = lynode domain node handler options
OBJ = $(addsuffix .o, $(FILE_BN))


.PHONY : all build clean


all : build


%.o : %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

#dependencies: $(OBJ:.o=.c)
#	$(CC) -M $^ > $@

#include dependencies


build : $(OBJ)
	$(CC) $(LDFLAGS) -o lynode lynode.o \
../util/misc.o ../util/luoyun.o ../util/disk.o \
domain.o node.o handler.o ../util/download.o options.o



test : build


clean :
	@$(RM) *.o lynode cscope.out *.log
