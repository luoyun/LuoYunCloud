#!/bin/sh

ln -sf /LuoYun/bin/pyosc/start /etc/rc3.d/S01luoyun-osconfig
ln -sf /LuoYun/bin/pyosm/start /etc/rc3.d/S90luoyun-osmanager
ln -sf /LuoYun/bin/webssh/start /etc/rc3.d/S99luoyun-webssh
ln -sf /LuoYun/bin/pyweb/start /etc/rc3.d/S99luoyun-web
