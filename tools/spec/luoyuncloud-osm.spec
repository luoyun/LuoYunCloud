
Name: luoyuncloud
Version: 0.5
Release: 9%{?dist}
Summary: the Cloud Computing software that can be used to build IaaS, SaaS or PaaS platforms
Group: Server/Cloud
License: GPLv2+
URL: http://www.luoyun.co            
Vendor: LuoYun Co.
Source0: luoyuncloud-0.5.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
LuoYunCloud is an easy-to-use Cloud Computing platform

%package osm
Summary: OS Manager
Group: Server/Cloud
Requires: python >= 2.6

%description osm
OS Manager for connecting LuoYunCloud

%prep
%setup -q

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
cp -rf osmanager %{buildroot}/LuoYun
mkdir -p %{buildroot}/etc/init
cp -rf osmanager/init/* %{buildroot}/etc/init/
mkdir %{buildroot}/LuoYun/log

%clean
rm -rf %{buildroot}

%preun osm
rm -f /LuoYun/log/luoyun.log /LuoYun/log/lyweb.log /LuoYun/conf/luoyun.conf
find /LuoYun/bin -name \*.py[co] -exec rm -f {} \;

%files osm
%defattr(-,root,root,-)
/LuoYun
/etc/init/luoyun
%config(noreplace) /LuoYun/custom
%config(noreplace) /LuoYun/build
%doc /LuoYun/README
%doc /LuoYun/bin/pyosm/README

%changelog
* Tue Apr 30 2013 Dongwu Zeng <dongwu@luoyun.co> - 0.5-9
- new init scripts

* Tue Dec 12 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-8
- rebase on luoyuncloud 0.5-8

* Tue Dec 11 2012 Dongwu Zeng <dongwu@luoyun.co> - 0.5-7
- initial build along with luoyuncloud 0.5-7
