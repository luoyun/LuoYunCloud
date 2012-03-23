TRACE_LEVEL=@TRACE_VAR@

#EXTRA_DIST = ding-libs-0.1.3.tar.gz

dingsrcdir = ./ding-libs
noinst_LIBRARIES = libding.a
libding_a_SOURCES = 

##############################################################################
# Common
##############################################################################
AM_CFLAGS = \
    -Wall -Wshadow -Wstrict-prototypes -Wpointer-arith -Wcast-qual \
    -Wcast-align -Wwrite-strings

AM_CPPFLAGS = \
    -I$(dingsrcdir)/collection \
    -I$(dingsrcdir)/path_utils \
    -I$(dingsrcdir)/refarray \
    -I$(dingsrcdir)/dhash \
    -I$(dingsrcdir)/ini \
    -I$(dingsrcdir) \
    -I$(dingsrcdir)/trace \
    $(TRACE_LEVEL)

INCLUES = -I$(top_srcdir)/

##############################################################################
# Path Utils
##############################################################################

libpath_utils_a_SOURCES = $(dingsrcdir)/path_utils/path_utils.c\
                          $(dingsrcdir)/path_utils/path_utils.h
libding_a_SOURCES += $(libpath_utils_a_SOURCES)

##############################################################################
# dhash
##############################################################################

libdhash_a_SOURCES = $(dingsrcdir)/dhash/dhash.c \
                     $(dingsrcdir)/dhash/dhash.h
libding_a_SOURCES += $(libdhash_a_SOURCES)

##############################################################################
# collection
##############################################################################

libcollection_a_SOURCES = \
    $(dingsrcdir)/collection/collection.c \
    $(dingsrcdir)/collection/collection_tools.c \
    $(dingsrcdir)/collection/collection_cnv.c \
    $(dingsrcdir)/collection/collection_queue.c \
    $(dingsrcdir)/collection/collection_stack.c \
    $(dingsrcdir)/collection/collection_cmp.c \
    $(dingsrcdir)/collection/collection_iter.c \
    $(dingsrcdir)/collection/collection_priv.h \
    $(dingsrcdir)/collection/collection_tools.h \
    $(dingsrcdir)/collection/collection_queue.h \
    $(dingsrcdir)/collection/collection.h \
    $(dingsrcdir)/collection/collection_stack.h \
    $(dingsrcdir)/trace/trace.h
libding_a_SOURCES += $(libcollection_a_SOURCES)

##############################################################################
# refarray
##############################################################################

libref_array_a_SOURCES = \
    $(dingsrcdir)/refarray/ref_array.c \
    $(dingsrcdir)/refarray/ref_array.h \
    $(dingsrcdir)/trace/trace.h
libding_a_SOURCES += $(libref_array_a_SOURCES)

##############################################################################
# ini_config
##############################################################################

libini_config_a_SOURCES = \
    $(dingsrcdir)/ini/ini_config.c \
    $(dingsrcdir)/ini/ini_config.h \
    $(dingsrcdir)/ini/ini_get_value.c \
    $(dingsrcdir)/ini/ini_get_array.c \
    $(dingsrcdir)/ini/ini_list.c \
    $(dingsrcdir)/ini/ini_print.c \
    $(dingsrcdir)/ini/ini_parse.c \
    $(dingsrcdir)/ini/ini_parse.h \
    $(dingsrcdir)/ini/ini_metadata.c \
    $(dingsrcdir)/ini/ini_metadata.h \
    $(dingsrcdir)/ini/ini_defines.h \
    $(dingsrcdir)/ini/ini_comment.c \
    $(dingsrcdir)/ini/ini_comment.h \
    $(dingsrcdir)/trace/trace.h
libding_a_SOURCES += $(libini_config_a_SOURCES)

##############################################################################
# Additional rules
##############################################################################
