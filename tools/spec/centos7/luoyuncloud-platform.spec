%define LUOYUN_HOME /opt/LuoYun/
%define LUOYUN_PLATFORM %{LUOYUN_HOME}platform/

Name: luoyuncloud
Version: 0.6.4
Release: 8%{?dist}
Summary: the Cloud Computing software that can be used to build IaaS, SaaS or PaaS platforms
Group: Server/Cloud
License: GPLv2+
URL: http://www.luoyun.co            
Vendor: LuoYun Co.
Source0: luoyuncloud-%{version}.tar.bz2
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

%install
rm -rf %{buildroot}
# install scripts
#mkdir -p %{buildroot}/opt/LuoYun/bin
#mkdir -p %{buildroot}/opt/LuoYun/install
#cp tools/lyclc %{buildroot}/opt/LuoYun/bin/ || exit 1
#cp tools/lynode %{buildroot}/opt/LuoYun/bin/ || exit 1
#cp tools/luoyun-service %{buildroot}/opt/LuoYun/bin/ || exit 1
#mkdir -p %{buildroot}/etc/init
#cp tools/init/* %{buildroot}/etc/init

# install platform
pushd platform/
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/etc/init.d
#ln -sf /opt/LuoYun/bin/luoyun-service %{buildroot}/etc/init.d/lyclc
#ln -sf /opt/LuoYun/bin/luoyun-service %{buildroot}/etc/init.d/lynode
popd

%clean
rm -rf %{buildroot}

%files clc
%defattr(-,root,root,-)
#%doc AUTHORS COPYING ChangeLog README TODO INSTALL LICENSE* fetch-*
#/etc/init.d/lyclc
#/etc/init/lyclc.conf
#%{LUOYUN_HOME}bin/luoyun-service
#%{LUOYUN_HOME}bin/lyclc
%{LUOYUN_PLATFORM}bin/lyclc
%config(noreplace) %{LUOYUN_PLATFORM}etc/luoyun-cloud/lyclc.conf

%files node
%defattr(-,root,root,-)
#/etc/init.d/lynode
#/etc/init/lynode.conf
#%{LUOYUN_HOME}bin/luoyun-service
#%{LUOYUN_HOME}bin/lynode
%{LUOYUN_PLATFORM}bin/lynode
%config(noreplace) %{LUOYUN_PLATFORM}etc/luoyun-cloud/lynode.conf

%changelog
* Sun Sep 07 2014 Dongwu Zeng <zendongwu@hotmail.com> - 0.6.4-8
- port 0.6.4-8 for EL6 to Centos 7

