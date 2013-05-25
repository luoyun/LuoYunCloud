单机部署 LuoYunCloud 防火墙设置
===============================

本文的单机部署 LuoYunCloud 的场景是：

1. 一台计算机，运行 lyweb, lyclc, lynode 服务程序
2. lynode 的网络环境没有特别设置过，使用的是 libvirtd 的默认虚拟内网

由于 libvirtd 默认使用的网络是通过 iptables 实现内部交换的，所以我们一
定要开启 Linux 的 iptables 服务才可以正常运行。

本文介绍这种环境下，我们还需要配置哪些 iptables 。

**注意** ： 如果使用 LuoYunCloud LiveCD 安装的系统，我们己经默认配置好
这些了，一般情况下您不需要知道下面所讲的。

Redhat ( RHEL, Fedora, CentOS ) 的防火墙设置文件是
`/etc/sysconfig/iptables` ， 这是单机部署，防火墙的一个配置示例 ::

  # Firewall configuration written by system-config-firewall
  # Manual customization of this file is not recommended.
  *filter
  :INPUT ACCEPT [0:0]
  :FORWARD ACCEPT [0:0]
  :OUTPUT ACCEPT [0:0]
  -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  -A INPUT -p icmp -j ACCEPT
  -A INPUT -i lo -j ACCEPT
  -A INPUT -i virbr0 -j ACCEPT
  -A INPUT -m state --state NEW -m tcp -p tcp --dport 21 -j ACCEPT
  -A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
  -A INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT
  -A INPUT -m state --state NEW -m tcp -p tcp --dport 8080 -j ACCEPT
  -A INPUT -m state --state NEW -m tcp -p tcp --dport 8001 -j ACCEPT
  -A INPUT -m state --state NEW -m tcp -p tcp --dport 1369 -j ACCEPT
  -A INPUT -m state --state NEW -m tcp -p tcp --dport 5900:6000 -j ACCEPT
  -A INPUT -j REJECT --reject-with icmp-host-prohibited
  -A FORWARD -j REJECT --reject-with icmp-host-prohibited
  COMMIT
  

上面开通了 21, 22, 80, 8080, 8001, 1369, 5900:6000 的端口，重启
iptables 服务就可以生效 ::

  /etc/init.d/iptables restart


