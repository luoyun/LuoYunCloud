%define LUOYUN_HOME /opt/LuoYun/
%define LUOYUN_PLATFORM %{LUOYUN_HOME}platform/

Name: luoyuncloud
Version: 0.5
Release: 13.1%{?dist}
Summary: the Cloud Computing software that can be used to build IaaS, SaaS or PaaS platforms
Group: Server/Cloud
License: GPLv2+
URL: http://www.luoyun.co            
Vendor: LuoYun Co.
Source0: luoyuncloud-0.5.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: zlib-devel,bzip2-devel,libcurl-devel,libvirt-devel,libxml2-devel,postgresql-devel,libuuid-devel,libgcrypt-devel

%description
LuoYunCloud is a software package that can be used to build different Cloud Computing platforms, e.g. IaaS, SaaS, PaaS, etc.
LuoYunCloud software package includes three main components, LuoYunCloud-clc, LuoYunCloud-node an LuoYunCloud-web.

%package clc
Summary: Cloud Control server for LuoYunCloud platform
Group: Server/Cloud

%description clc
This rpm includes Cloud Control server for LuoYunCloud platform. A LuoYunCloud Cloud Computing platform must have one active Cloud Control server.

%package node
Summary: Node server for LuoYunCloud platform
Group: Server/Cloud
Requires: qemu-kvm, bridge-utils, libvirt

%description node
This rpm includes Node server for LuoYunCloud platform. A LuoYunCloud Cloud Computing platform must have one and more Node servers.
The LuoYunCloud Cloud Control server can coexist with Node server on a physical machine.

%package web
Summary: Web server for LuoYunCloud platform
Group: Server/Cloud
Requires: python >= 2.6, python-psycopg2, python-dateutil, postgresql-server, python-imaging, gettext, luoyuncloud-nginx
BuildRequires: unzip, python, postgresql-server, postgresql

%description web
This rpm includes Web server for LuoYunCloud platform. A LuoYunCloud Cloud Computing platform must have one active Web server. 

%package nginx
Summary: Custom nginx web server for LuoYunCloud platform
Group: Server/Cloud
BuildRequires: pcre-devel openssl-devel

%description nginx
This a custom nginx for LuoYunCloud platform, contain nginx_upload_module and nginx-upload-progress.

%prep
%setup -q

%build
# build platform
pushd platform/
%configure --prefix=%{LUOYUN_PLATFORM} \
    --bindir=%{LUOYUN_PLATFORM}/bin \
    --sysconfdir=/etc/luoyun-cloud
make %{?_smp_mflags}
popd

# build nginx
pushd nginx/nginx
./configure --prefix=/etc/nginx \
    --sbin-path=/usr/sbin/nginx \
    --pid-path=/var/run/nginx.pid \
    --lock-path=/var/lock/nginx.lock \
    --http-client-body-temp-path=/var/spool/nginx/client_body_temp \
    --http-proxy-temp-path=/var/spool/nginx/proxy_temp \
    --http-fastcgi-temp-path=/var/spool/nginx/fastcgi_temp \
    --http-log-path=/var/log/nginx/access.log \
    --error-log-path=/var/log/nginx/error.log \
    --user=luoyun --group=luoyun \
    --with-imap \
    --with-imap_ssl_module \
    --with-http_ssl_module \
    --with-http_stub_status_module \
    --with-http_dav_module \
    --with-http_gzip_static_module \
    --with-ipv6 \
    --http-scgi-temp-path=/var/spool/nginx \
    --http-uwsgi-temp-path=/var/spool/nginx \
    --add-module=../nginx_upload_module \
    --add-module=../nginx-upload-progress
make
popd

%install
rm -rf %{buildroot}
# install scripts
mkdir -p %{buildroot}/opt/LuoYun/bin
mkdir -p %{buildroot}/opt/LuoYun/install
cp tools/install-web-0.5.sh %{buildroot}/opt/LuoYun/install/install-web.sh || exit 1
cp tools/lyclc %{buildroot}/opt/LuoYun/bin/ || exit 1
cp tools/lynode %{buildroot}/opt/LuoYun/bin/ || exit 1
cp tools/lyweb %{buildroot}/opt/LuoYun/bin/ || exit 1
cp tools/luoyun-service %{buildroot}/opt/LuoYun/bin/ || exit 1
mkdir -p %{buildroot}/etc/init
cp tools/init/* %{buildroot}/etc/init

# install platform
pushd platform/
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/etc/init.d
ln -sf /opt/LuoYun/bin/luoyun-service %{buildroot}/etc/init.d/lyclc
ln -sf /opt/LuoYun/bin/luoyun-service %{buildroot}/etc/init.d/lynode
popd

# install nginx
pushd nginx/nginx
make DESTDIR=%{buildroot} install
cp ../../tools/nginx.conf.example %{buildroot}/etc/nginx/conf/nginx.conf
popd

# install web
cp -rf lyweb %{buildroot}/opt/LuoYun/web
ln -sf /opt/LuoYun/bin/luoyun-service %{buildroot}/etc/init.d/lyweb
python %{buildroot}/opt/LuoYun/web/manage.py --i18n
pushd %{buildroot}/opt/LuoYun/web/lib/
chmod u+x ../site.py
popd

%clean
rm -rf %{buildroot}

%post nginx
# nginx
mkdir -pv /var/{spool,log}/nginx/
mkdir -pv /opt/LuoYun/data/{upload,appliance} /opt/LuoYun/logs/
id luoyun &> /dev/null || useradd luoyun -s /sbin/nologin

%files clc
%defattr(-,root,root,-)
#%doc AUTHORS COPYING ChangeLog README TODO INSTALL LICENSE* fetch-*
/etc/init.d/lyclc
/etc/init/lyclc.conf
%{LUOYUN_HOME}bin/luoyun-service
%{LUOYUN_HOME}bin/lyclc
%{LUOYUN_PLATFORM}bin/lyclc
%config(noreplace) %{LUOYUN_PLATFORM}etc/luoyun-cloud/lyclc.conf

%files node
%defattr(-,root,root,-)
/etc/init.d/lynode
/etc/init/lynode.conf
%{LUOYUN_HOME}bin/luoyun-service
%{LUOYUN_HOME}bin/lynode
%{LUOYUN_PLATFORM}bin/lynode
%config(noreplace) %{LUOYUN_PLATFORM}etc/luoyun-cloud/lynode.conf

%files web
%defattr(-,root,root,-)
/etc/init.d/lyweb
/etc/init/lyweb.conf
%{LUOYUN_HOME}bin/lyweb
%{LUOYUN_HOME}bin/luoyun-service
%{LUOYUN_HOME}install/install-web.sh
%{LUOYUN_HOME}web/

%files nginx
%defattr(-,root,root,-)
/etc/init/nginx.conf
/usr/sbin/nginx
/etc/nginx



%changelog
* Sun May 19 2013 Dongwu Zeng <dongwu@luoyun.co> - 0.5-13.1
- skip interface/network type checking
- missing nginx.conf init file

* Sat May 18 2013 Dongwu Zeng <dongwu@luoyun.co> - 0.5-13
- updated lyweb
- graphics password support
- instance network stat support

* Sat May 11 2013 Dongwu Zeng <dongwu@luoyun.co> - 0.5-12.2
- fix bug for graphics port support in reboot action

* Fri May 10 2013 Dongwu Zeng <dongwu@luoyun.co> - 0.5-12.1
- graphics port support

* Tue May 01 2013 Dongwu Zeng <dongwu@luoyun.co> - 0.5-12
- improve batch job processing
- new init scripts

* Tue Jan 22 2013 Dongwu Zeng <dongwu@luoyun.co> - 0.5-11
- CLC node_select for every VM start
- temporarily hold VM resource

* Tue Dec 17 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-10
- update web Chinese translation

* Tue Dec 11 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-9
- update web Chinese translation

* Tue Dec 11 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-8
- fix web Chinese display

* Tue Dec 11 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-7
- fix nginx upload problem
- fix lyweb terminal display problem
- check postgresql twice

* Mon Dec 10 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-6
- move install-web.sh /opt/LuoYun/install
- use symbolic link for lyclc, lyweb, lynode

* Sun Dec  9 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-5
- update install-web.sh

* Thu Dec  6 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-4
- update lyweb

* Thu Dec  6 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-3
- Include install-web.sh in web

* Thu Dec  6 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-2
- Updated lyclc, lynode and lyweb scripts

* Thu Nov 21 2012 Li Jian <lijian@luoyun.co> - 0.5-1
- For 0.5

* Thu Sep 20 2012 Li Jian <lijian@luoyun.co> - 0.4-1
- Initial release

