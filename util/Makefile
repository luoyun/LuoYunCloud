CC = gcc
CFLAGS = -Wall -g -std=c99 -D_POSIX_C_SOURCE=200112
LDFLAGS = -lm

SC_SRC_DIR := $(if $(SC_SRC_DIR),$(SC_SRC_DIR),../)
INCLUDES := -I $(SC_SRC_DIR) -I$(shell pg_config --includedir)

RM = /bin/rm -f

# FILE_BN : file basename
UTIL_FILE_BN = misc luoyun download disk
UTIL_OBJ = $(addsuffix .o, $(UTIL_FILE_BN))

.PHONY : build clean


%.o : %.h
%.o : %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

all : build

build : $(UTIL_OBJ)

clean :
	@$(RM) *.o cscope.out
