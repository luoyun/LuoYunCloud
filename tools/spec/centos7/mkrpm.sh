#!/bin/sh
thispwd=$(dirname $0)
[ -z "$thispwd" ] && thispwd=.
pushd $thispwd/../../../platform
[ -e Makefile ] && make distclean
rm -rf src/osmanager/.deps/
rm -f src/osmanager/Makefile
popd

thisver=$(cat $thispwd/luoyuncloud-platform.spec | awk '/^Version:/ {print $2}')
[ -z "$thisver" ] && echo "Error: can not find version" && exit 1
rm -rf /tmp/luoyuncloud-$thisver
mkdir /tmp/luoyuncloud-$thisver
cp -a $thispwd/../../../* /tmp/luoyuncloud-$thisver
pushd /tmp
[ -e '~/rpmbuild/SOURCES' ] || mkdir -p ~/rpmbuild/SOURCES
tar cjf ~/rpmbuild/SOURCES/luoyuncloud-$thisver.tar.bz2 luoyuncloud-$thisver
popd
rpmbuild -ba $thispwd/luoyuncloud-platform.spec 
