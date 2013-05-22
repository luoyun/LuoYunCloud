.. _install-yum:

使用 yum 源安装
-------------------------
.. note::
 
   本安装步骤适用于 RHEL/CentOS 6.x 64 位操作系统

为了方便大家更好的体验和部署 LuoYunCould 云计算系统，我们提供了 yum install 安装方式供大家使用。您只需要掌握 yum install 即可在您的计算机中快速的部署 LuoYunCloud 了。 

.. note::

   以下所有操作请使用 root 权限的帐户进行。

1. 将 LuoYunCloud 加入您的软件源中 ::

     wget http://dl.luoyun.co/LuoYunCloud/0.5/RPMS/el6/x86_64/luoyuncloud.repo
     mv luoyuncloud.repo /etc/yum.repos.d/luoyuncloud.repo

#. 部署 LuoYunCloud 的主控服务器软件 ::

     yum install luoyuncloud-web luoyuncloud-clc luoyuncloud-nginx

   执行此条指令可以在您的机器上部署 lyweb 和 lyclc 这两项 LuoYunCloud 服务。

   执行完成后，这两项服务已经默认部署在 /opt/LuoYun 中，接下来您需要执行一次 lyweb 的安装。

3. 安装 lyweb 服务及 postgresql 数据库

   执行： ::

     /opt/LuoYun/install/install-web.sh

   此指令将帮助您快速的完成 lyweb 服务及数据库的初始化安装。在执行过程中您需要输入数据库名称，建议使用 luoyun，输入2次后，将请求给以 luoyun 数据库高级权限，请输入 y 确认。

   得到如下反馈后,表示您的机器中已经安装 lyweb 及其所需要的数据库： ::
     
     [root@localhost ~]# /opt/LuoYun/install/install-web.sh
     Initializing database:                                     [  OK  ]   # 注意，此处可能需要时间较长，请耐心等待即可。
     Starting postgresql service:                               [  OK  ]
     Create DB User
     Enter password for new role:                                          # 此处请输入luoyun
     Enter it again:                                                       # 再输入一次luoyun进行确认
     Shall the new role be a superuser? (y/n)                              # 输入y，确认数据库权限
     => [DD] create user luoyun succeed
     Create DB luoyun
     => [DD] create luoyun succeed
     Stopping postgresql service:                               [  OK  ]
     Starting postgresql service:                               [  OK  ]
     DEBUG:Manage:build /opt/LuoYun/web/locale/zh_CN/LC_MESSAGES/luoyun.mo success
     DEBUG:Manage:build /opt/LuoYun/web/locale/zh_CN/LC_MESSAGES/app.mo success
     DEBUG:Manage:build /opt/LuoYun/web/locale/en_US/LC_MESSAGES/luoyun.mo success
     DEBUG:Manage:build /opt/LuoYun/web/locale/en_US/LC_MESSAGES/app.mo success
     [root@localhost ~]#

   至此，上述提示信息即表示您已经成功完成 lyweb 的安装。

   .. note::

      如果安装过程中出现错误提示，请执行下面的两条指令对数据库进行重置 
      ::
   
	 # service postgresql stop

	 # rm -rf /var/lib/pgsql/*

      然后重新执行

      ::
   
	 /opt/LuoYun/install/install-web.sh 

#. 启动 lyweb 服务

   确定 postgresql 数据库已经启动。如未启动，用如下命令启动数据库 ::
     
     service postgresql start

   然后启动 lyweb ::

     service lyweb start
     
   系统将显示 ::

     Starting lyweb:   OK
   
   表示 lyweb 服务已经成功启动。用户可通过浏览器访问当然机器上的 LuoYunCloud 了。 

#. 启动 lyclc 服务 ::

     service lyclc start

   系统将显示 ::

     Starting lyclc:   OK

   表示机器上的 lyclc 服务启动成功，开始等待 lynode 服务器加入后开始提供创建虚拟机等服务。
   然后请执行下面的指令，打开 iptabe 的端口： ::

     iptables -I INPUT 1 -p tcp -m tcp --dport 1369 -j ACCEPT
     iptables -I INPUT 1 -p tcp -m tcp --dport 80 -j ACCEPT
     iptables -I INPUT 1 -p tcp -m tcp --dport 8080 -j ACCEPT
     iptables -I INPUT 1 -p tcp -m tcp --dport 8001 -j ACCEPT

      
#. 部署 LuoYunCloud 的节点服务器软件 ::

     yum install luoyuncloud-node

   执行完成即可。 

#. 启动 lynode 节点服务 ::

     service lynode start

   系统将显示 ::

     Starting lynode:   OK

   表示机器上的 lynode 服务启动成功。

   至此，当前机器已经可以提供完整的 LuoYunCloud 云计算服务了。 

#. 最后，将 LuoYunCloud 的各项服务配置成开机自启动

   首先，确定 iptables （防火墙）打开了如下端口。确定文件 /etc/sysconfig/iptables 包含以下内容。 ::

     -A INPUT -p tcp -m tcp --dport 1369 -j ACCEPT
     -A INPUT -p tcp -m tcp --dport 80 -j ACCEPT
     -A INPUT -p tcp -m tcp --dport 8001 -j ACCEPT
     -A INPUT -p tcp -m tcp --dport 8080 -j ACCEPT

   由于 iptables 规则顺序的执行方法，以上内容要在 ::

     -A INPUT -j REJECT --reject-with icmp-host-prohibited

   这条规则之上。

   然后, 请执行下列命令将各项所需要的服务加入系统的自动启动列表。 ::

     chkconfig postgresql on
     chkconfig lyweb on
     chkconfig lyclc on
     chkconfig lynode on
   
   加入成功后可以使用 chkconfig --list 查看服务自启动状态 ::

     # chkconfig --list lyweb
     lyweb           0:关闭  1:关闭  2:启用  3:启用  4:启用  5:启用  6:关闭
     # chkconfig --list lyclc
     lyclc           0:关闭  1:关闭  2:启用  3:启用  4:启用  5:启用  6:关闭
     # chkconfig --list lynode
     lynode          0:关闭  1:关闭  2:启用  3:启用  4:启用  5:启用  6:关闭
     # chkconfig --list postgresql
     postgresql      0:关闭  1:关闭  2:启用  3:启用  4:启用  5:启用  6:关闭

     
   至此，LuoYunCloud 可以在系统启动后，自动启动。 
