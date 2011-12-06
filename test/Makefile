CC = gcc
CFLAGS = -Wall -g -std=c99
LDFLAGS = -lm -pthread -lcurl -lbz2 -lz

SC_SRC_DIR := $(if $(SC_SRC_DIR),$(SC_SRC_DIR),../)
INCLUDES := -I $(SC_SRC_DIR) -I$(shell pg_config --includedir)

RM = /bin/rm -f

# FILE_BN : file basename
UTIL_FILE_BN = t_util_bunzip t_util_print_dpt
UTIL_OBJ = $(addsuffix .o, $(UTIL_FILE_BN))

.PHONY : build clean


%.o : %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

all : build

build : $(UTIL_OBJ)
	$(CC) $(LDFLAGS) -o t_util_bunzip.bin t_util_bunzip.o ../util/*.o
	$(CC) $(LDFLAGS) -o t_util_print_dpt.bin t_util_print_dpt.o ../util/*.o

clean :
	@$(RM) *.o cscope.out *.bin
