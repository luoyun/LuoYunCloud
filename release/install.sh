#!/bin/sh

id=$(id -u)

if [ "$id" -ne 0 ]
then
  echo "Must be root to install. Install failed"
  exit 1
fi

release=
a=$(</etc/redhat-release)
if [ "$a" != "${a%release 6*}" ]
then
  echo "OS is RHEL/CentOS 6"
  release=6
elif [ "$a" != "${a%release 5*}" ] 
then 
  echo "OS is RHEL/CentOS 5"
  release=5
else
  a=$(ldd /usr/bin/curl | grep libcurl | head -n 1 | awk '{printf $1}')
  [ "$a" == "libcurl.so.3" ] && release=5
  [ "$a" == "libcurl.so.4" ] && release=6
  echo "OS is not a supported RHEL/CentOS 5/6 distro"
  if [ -n "$release" ]
  then
    echo "Best guess is made"
  else
    echo "Installation is aborted!"
    exit 1
  fi
fi

tar=luoyun-cloud-0.2-bin-${release}.tgz

clc=$(tar tzf $tar | grep clc\$)
node=$(tar tzf $tar | grep node\$)

tar -xzf luoyun-cloud-0.2-bin-${release}.tgz -C /

if [ $? -eq 0 ]
then
  echo "Installation succeeds!"
  echo "Please run 'sudo /"$clc"' to start Cloud Controller daemon"
  echo "Please run 'sudo /"$node"' to start Node Server daemon"
  exit 0
else
  echo "Installation failed!"
  exit 1
fi
