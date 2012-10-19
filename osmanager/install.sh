#!/bin/bash

for r in 2 3 4 5
do
  ln -sf /LuoYun/osmanager.sh /etc/rc${r}.d/S99luoyun-osmanager
done
