CC = gcc
CFLAGS = -Wall -g -std=c99
LDFLAGS = -lm
export SC_TOP_DIR := $(PWD)
export SC_SRC_DIR := $(PWD)


RM = /bin/rm -f


#SUBDIRS = node clc util
SUBDIRS = util control compute test osmanager

.PHONY : all build clean clean-all

all : build


build:
	@for subdir in $(SUBDIRS); do \
	(cd $$subdir && $(MAKE) $@) || exit $$? ; done

clean:
	@$(RM) *.log
	@for subdir in $(SUBDIRS); do \
	(cd $$subdir && $(MAKE) $@ -s) || exit $$? ; done
