#!/bin/bash

### BEGIN INIT INFO
# Provides:          osmanager
# Required-Start:    
# Required-Stop:
# Should-Start:
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: start LuoYun OS manager
# Description:       LuoYun OS manager configures essential system settings
#                    such as root password, network address, etc. It also
#                    starts a simple web server and web ssh client, and
#                    maintains connection with LuoYun Cloud Controller.
### END INIT INFO

unalias -a

EXE=$(readlink $0)
[ -z "$EXE" ] && EXE=$0
luoyundir=$(dirname $EXE)
exedir=${luoyundir}/bin
customdir=${luoyundir}/custom
confdir=${luoyundir}/conf
confpath=$confdir/luoyun.conf
logdir=${luoyundir}/log

myexit()
{
    [ -n "$1" ] && echo $1
    exit 1
}

mystart()
{
    [ -z "$1" ] && echo "osmanger warning: missing argument" && return
    [ ! -x "$1" ] && echo "osmanger warning: $1 not executable" && return
    echo $*
    $*
    return $?
}

tmpmntdir=
mntdir=
mntinfo=$(mount | grep '/dev/fd0')
if [ $? -eq 0 ]
then
    mntdir=$(echo ${mntinfo} | awk '{print $3}')
else
    module=$(lsmod | grep -w floppy | awk "{print $1}")
    [ "$module" == "floppy" ] || modprobe floppy || myexit "osmanager error: failed load kerne module"
    tmpmntdir=$(mktemp -d /tmp/osmanger.XXXXXX)
    [ $? ] || myexit "osmanger error: failed create temp dir"
    mntdir=$tmpmntdir 
    mount /dev/fd0 $mntdir || (sleep 2 && mount /dev/fd0 $mntdir ) || myexit "osmanger error: failed mount /dev/fd0 $mntdir"
fi
[ -f "$mntdir/luoyun.ini" ] || myexit "osmanger error: $mntdir/luoyun.ini not found"

newconf=1
if [ ! -d "$confdir" ]
then
    mkdir -p $confdir || myexit "osmanger error: failed mkdir $confdir"
elif [ -f "$confpath" ]
then
    cmp -s "$mntdir/luoyun.ini" "$confpath" && newconf=0
fi
[ $newconf -eq 0 ] || cp "$mntdir/luoyun.ini" "$confpath" || myexit "osmanger error: failed copy $confpath"
umount /dev/fd0 && [ -n "$tmpmntdir" ] && rmdir $tmpmntdir 

# create log directory
[ -d "$logdir" ] ||  mkdir -p $logdir || myexit "osmanger error: failed mkdir $logdir"

# start osconfig
exepath=${exedir}/pyosc/osconfig.py
if [ -x "$exepath" ]
then
    echo "Start $exepath"
    $exepath
    sleep 2
fi

# run application specific config scripts
exepath=${customdir}/scripts/config
if [ -x "$exepath" ]
then
    echo "run $exepath"
    $exepath
    sleep 2
fi

# start lyweb
exepath=${exedir}/pyweb/lyweb.py
if [ -x "$exepath" ]
then
    echo "Start $exepath"
    $exepath 8080 &
fi

# start webssh
exepath=${exedir}/webssh/webssh.py
if [ -x "$exepath" ] 
then 
    echo "Start $exepath" 
    $exepath
fi

# start lyosm
exepath=${exedir}/pyosm/lyosm.py
if [ -x "$exepath" ]
then 
    echo "Start $exepath"
    $exepath &
fi

