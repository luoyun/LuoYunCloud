#!/bin/bash

unalias -a

luoyundir=/LuoYun
exedir=${luoyundir}/bin
customdir=${luoyundir}/custom
confdir=${luoyundir}/conf
confpath=$confdir/luoyun.conf
logdir=${luoyundir}/log

myexit()
{
    [ -n "$1" ] && echo -e "$1\r"
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
echo -e "Start $exepath\r"
$exepath
