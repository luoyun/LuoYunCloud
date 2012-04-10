# Copyright (C) 2012 LuoYun Co. <admin@luoyun.co>
#  
# This file is free software; as a special exception the author gives
# unlimited permission to copy and/or distribute it, with or without 
# modifications, as long as this notice is preserved.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, to the extent permitted by law; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

AC_INIT([luoyun-cloud],
        [0.2],
        [LuoYun Co. zengdongwu@hotmail.com])
AC_CONFIG_AUX_DIR(config)
AM_CONFIG_HEADER(config.h)
AM_INIT_AUTOMAKE([dist-bzip2])

AC_PROG_CC([cc gcc])
CFLAGS="-Wall -Werror -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
AC_PROG_RANLIB
AC_PROG_INSTALL

# Checks for libraries.
AC_CHECK_LIB([z], [gzopen], [], [ echo "libz is not found"; exit -1])
AC_CHECK_LIB([bz2], [BZ2_bzReadOpen], [], [ echo "libbz2 is not found"; exit -1])
AC_CHECK_LIB([curl], [curl_global_init], [], [ echo "libcurl is not found"; exit -1])
AC_CHECK_LIB([virt], [virConnectOpen], [], [ echo "libvirt is not found"; exit -1])
AC_CHECK_LIB([xml2], [xmlReadDoc], [], [ echo "libxml2 is not found"; exit -1])
AC_CHECK_LIB([pq], [PQconnectdb], [], [ echo "libpq is not found"; exit -1])
AC_CHECK_LIB([uuid], [uuid_generate], [], [ echo "libuuid is not found"; exit -1])
AC_CHECK_LIB([gcrypt], [gcry_control], [], [ echo "libgcrypt is not found"; exit -1])

# ding-libs
system_dinglib=no
AC_ARG_ENABLE([system-dinglib],
              [AS_HELP_STRING([--enable-system-dinglib, don't use dinglib that comes with luoyun-cloud, use libini_config and libcollection provided by OS])],
              [system_dinglib=yes
               AC_CHECK_LIB([ini_config], [config_from_file], [], [ echo "libini_config is not found"; exit -1])],
              [system_dinglib=no
               if ! test -e lib/ding-libs; then 
                   echo "Please create symbolic link lib/ding-libs to point to uncompressed ding-libs source directories"
                   echo "For example, assuming ding-libs-0.1.3.tar.gz is uncompressed in lib, do ln -sf ding-libs-0.1.3 lib/ding-libs" 
                   exit -1
               fi])
if ! test -e lib/ding-libs -a x"$system_dinglib"="xno"; then
    AC_MSG_WARN([Please create symbolic link lib/ding-libs to point to uncompressed ding-libs source directories])
    AC_MSG_ERROR([For example, assuming ding-libs-0.1.3.tar.gz is uncompressed in lib, do ln -sf ding-libs-0.1.3 lib/ding-libs])
fi


# lynode data dir
AS_IF([test ["$prefix" == "NONE"] ], [DEFAULT_LYNODE_DATA_DIR="/opt/lynode_data"], [DEFAULT_LYNODE_DATA_DIR="${prefix%/}/node_data"])
AC_SUBST(DEFAULT_LYNODE_DATA_DIR)
AC_DEFINE_UNQUOTED([DEFAULT_LYNODE_DATA_DIR], ["${DEFAULT_LYNODE_DATA_DIR}"], [default lynode data dir])

# lyclc data dir
AS_IF([test ["$prefix" == "NONE"] ], [DEFAULT_LYCLC_DATA_DIR="/opt/clc_data"], [DEFAULT_LYCLC_DATA_DIR="${prefix%/}/clc_data"])
AC_SUBST(DEFAULT_LYCLC_DATA_DIR)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_DATA_DIR], ["${DEFAULT_LYCLC_DATA_DIR}"], [default lyclc data dir])

# lynode log file
AS_IF([test ["$prefix" == "NONE"] ], [DEFAULT_LYNODE_LOG_PATH="/var/log/lynode.log"], [DEFAULT_LYNODE_LOG_PATH="${prefix%%/}/logs/lynode.log"])
AC_SUBST(DEFAULT_LYNODE_LOG_PATH)
AC_DEFINE_UNQUOTED([DEFAULT_LYNODE_LOG_PATH], ["${DEFAULT_LYNODE_LOG_PATH}"], [default lynode log file])

# lyclc log file
AS_IF([test ["$prefix" == "NONE"] ], [DEFAULT_LYCLC_LOG_PATH="/var/log/lyclc.log"], [DEFAULT_LYCLC_LOG_PATH="${prefix%%/}/logs/lyclc.log"])
AC_SUBST(DEFAULT_LYCLC_LOG_PATH)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_LOG_PATH], ["${DEFAULT_LYCLC_LOG_PATH}"], [default clc log file])

# luoyun config dir
AS_IF([test ["$prefix" == "NONE"] ], [LYSYSCONFDIR=/etc/${PACKAGE_NAME}], [LYSYSCONFDIR=${prefix%%/}/etc/${PACKAGE_NAME}])
AC_SUBST(LYSYSCONFDIR)
AC_DEFINE_UNQUOTED([LYSYSCONFDIR], ["${LYSYSCONFDIR}"], [default config directory])

# lynode.conf
DEFAULT_LYNODE_CONF_PATH=${LYSYSCONFDIR%%/}/lynode.conf
AC_DEFINE_UNQUOTED([DEFAULT_LYNODE_CONF_PATH], ["${DEFAULT_LYNODE_CONF_PATH}"], [default lynode.conf location])

# lynode.sysconf
DEFAULT_LYNODE_SYSCONF_PATH=${LYSYSCONFDIR%%/}/lynode.sysconf
AC_SUBST(DEFAULT_LYNODE_SYSCONF_PATH)
AC_DEFINE_UNQUOTED([DEFAULT_LYNODE_SYSCONF_PATH], ["${DEFAULT_LYNODE_SYSCONF_PATH}"], [default lynode.sysconf location])

# lynode.uuid
DEFAULT_LYNODE_UUID_PATH=${LYSYSCONFDIR%%/}/lynode.uuid
AC_SUBST(DEFAULT_LYNODE_UUID_PATH)
AC_DEFINE_UNQUOTED([DEFAULT_LYNODE_UUID_PATH], ["${DEFAULT_LYNODE_UUID_PATH}"], [default lynode.uuid location])

# OSM luoyun.conf
DEFAULT_LYOSM_CONF_PATH=/LuoYun/conf/luoyun.conf
AC_SUBST(DEFAULT_LYOSM_CONF_PATH)
AC_DEFINE_UNQUOTED([DEFAULT_LYOSM_CONF_PATH], ["${DEFAULT_LYOSM_CONF_PATH}"], [default lyosm configration file path])

# OSM luoyun.key
DEFAULT_LYOSM_KEY_PATH=/LuoYun/conf/luoyun.key
AC_SUBST(DEFAULT_LYOSM_KEY_PATH)
AC_DEFINE_UNQUOTED([DEFAULT_LYOSM_KEY_PATH], ["${DEFAULT_LYOSM_KEY_PATH}"], [default lyosm secret key file path])

# lyclc.conf
DEFAULT_LYCLC_CONF_PATH=${LYSYSCONFDIR%%/}/lyclc.conf
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_CONF_PATH], ["${DEFAULT_LYCLC_CONF_PATH}"], [default lyclc.conf location])

# lyclc.uuid
DEFAULT_LYCLC_UUID_PATH=${LYSYSCONFDIR%%/}/lyclc.uuid
AC_SUBST(DEFAULT_LYCLC_UUID_PATH)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_UUID_PATH], ["${DEFAULT_LYCLC_UUID_PATH}"], [default lyclc.uuid location])

# default tcp/ip addresses
DEFAULT_NODE_PORT=3260
AC_SUBST(DEFAULT_NODE_PORT)
AC_DEFINE_UNQUOTED([DEFAULT_LYNODE_PORT], [${DEFAULT_NODE_PORT}], [default compute node port])
DEFAULT_CLC_PORT=1369
AC_SUBST(DEFAULT_CLC_PORT)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_PORT], [${DEFAULT_CLC_PORT}], [default cloud controller port])
DEFAULT_CLC_MCAST_PORT=1369
AC_SUBST(DEFAULT_CLC_MCAST_PORT)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_MCAST_PORT], [${DEFAULT_CLC_MCAST_PORT}], [default cloud controller mcast port])
DEFAULT_CLC_MCAST_IP=228.0.0.1
AC_SUBST(DEFAULT_CLC_MCAST_IP)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_MCAST_IP], ["${DEFAULT_CLC_MCAST_IP}"], [default cloud controller mcast ip])

# default DB settings
DEFAULT_CLC_DB_NAME=luoyun
AC_SUBST(DEFAULT_CLC_DB_NAME)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_DB_NAME], ["${DEFAULT_CLC_DB_NAME}"], [default db name])
DEFAULT_CLC_DB_USER=luoyun
AC_SUBST(DEFAULT_CLC_DB_USER)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_DB_USER], ["${DEFAULT_CLC_DB_USER}"], [default db user])
DEFAULT_CLC_DB_PASS=luoyun
AC_SUBST(DEFAULT_CLC_DB_PASS)
AC_DEFINE_UNQUOTED([DEFAULT_LYCLC_DB_PASS], ["${DEFAULT_CLC_DB_PASS}"], [default db user password])

# from ding-libs
# Enable trace build
AC_ARG_ENABLE([trace],
              [AS_HELP_STRING([--enable-trace[=LEVEL]],[build with low level tracing enabled])],
              [trace_level="$enableval"],
              [trace_level="0"])
AS_IF([test ["$trace_level" -gt "0"] -a ["$trace_level" -lt "8"] ],[AC_SUBST([TRACE_VAR],["-DTRACE_LEVEL=$trace_level"])])

AC_CHECK_SIZEOF([long])
AC_CHECK_SIZEOF([long long])

AC_CHECK_FUNC([strcasestr],
              AC_DEFINE([HAVE_STRCASESTR],
                        [1],
                        [Define if strcasestr exists]),
              AC_MSG_ERROR("Platform must support strcasestr"))

AC_DEFINE([COL_MAX_DATA], [65535], [Max length of the data block allowed in the collection value.])

AC_DEFINE([MAX_KEY], [1024], [Max length of the key in the INI file.])
# end from ding-libs

AC_CONFIG_FILES([
   Makefile
   README
   doc/Makefile
   m4/Makefile
   lib/Makefile
   conf/Makefile
   conf/lynode.conf
   conf/lyclc.conf
   src/Makefile
   src/util/Makefile
   src/compute/Makefile
   src/osmanager/Makefile
   src/clc/Makefile
   src/luoyun/Makefile
   tools/restart
   tools/stop
   tools/start
])

AC_OUTPUT
