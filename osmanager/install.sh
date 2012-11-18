#!/bin/bash

OSMEXEC=/LuoYun/osmanager.sh
for r in 2 3 4 5
do
  ln -sf "$OSMEXEC" /etc/rc${r}.d/S99luoyun-osmanager
done

res=0
for r in 2 3 4 5
do
  prog=
  [ -h "/etc/rc${r}.d/S99luoyun-osmanager" ] && prog=$(readlink /etc/rc${r}.d/S99luoyun-osmanager)
  [ "$prog" != "$OSMEXEC" ] && res=1 && break
done

[ "$res" -eq 0 ] && echo "osmanager is installed successfully, please restart system." && exit 0
echo "osmanager installation failed, please report to contact@luoyun.co"
exit 1
