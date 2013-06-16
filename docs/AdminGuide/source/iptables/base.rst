iptables 基本操作
=======================

本文介绍如使配置、应用、管理 iptables 。



如何修改 iptables 配置并应用？
------------------------------------

有如下方法:

1. 配置系统配置文件

   Redhat ( RHEL, Fedora, CentOS 等 ) 配置文件是
   `/etc/sysconfig/iptables`

   我们按照需求修改后，运行下面命令重启 iptables 服务 ::

	 /etc/init.d/iptables restart

2. 使用 iptables-save 和 iptables-restore 命令

   iptables-save 可以导出系统当前的 iptables 设置 ::

	 iptables-save > t

   编辑文件 t , 用 iptables-restore 命令应用到系统 ::

	 iptables-restore < t

3. 使用 iptables 命令

   你会发现 `/etc/sysconfig/iptables` 和 `iptables-save` 导出的文件中每
   一行的语法类似，其实这些语法也可以直接用 iptables 命令生效 ::

	 iptables -A INPUT -m state --state NEW -m tcp -p tcp --dport 8080 -j ACCEPT

