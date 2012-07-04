
noinst_LIBRARIES = libjson_parser.a
libjson_parser_a_SOURCES = ./json.c ./json.h

AM_CFLAGS = -g -O -std=gnu99 -D_GNU_SOURCE

noinst_PROGRAMS = test
test_SOURCES = test.c
test_LDADD = libjson_parser.a

