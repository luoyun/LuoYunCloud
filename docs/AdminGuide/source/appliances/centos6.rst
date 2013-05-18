基于 CentOS6 的应用制作及 OSManager 的安装
========================================================================

CentOS6 是 LuoYunCloud 应用所使用的主要 Linux 操作系统。下面介绍如何在 CentOS6 下安装 OSManager ，并制作成应用。

创建 CentOS6 虚拟机
-------------------------------------

用户可以选择任何一种虚拟化软件开发虚拟机。如使用 CentOS6 提供的 Virt-Manager 创建虚拟机并安装、配置用户所需的应用软件。

LuoYunCloud对需要制作成应用的虚拟机有如下要求:

- 虚拟机使用单一的虚拟磁盘

- 虚拟磁盘需设置为 RAW 格式

为便于调试，我们建议对虚拟机内的CentOS6操作系统做如下配置。用户可根据自身需要，决定是否采用相关建议。

- 支持在串行口（ttyS0）显示操作系统控制终端

- 虚拟磁盘不使用 LVM，直接创建为 SCSI 磁盘（/dev/sda）

- 虚拟磁盘有两个分区（/dev/sda1, /dev/sda2)，前一分区包含所有系统和应用软件，后一分区为 Swap

安装 OSManager
-------------------------------

OSManager 是将虚拟机与 LuoYunCloud 云计算平台相连接的软件。最新的 OSManager 的安装包可以在 `这里 <http://dl.luoyun.co/LuoYunCloud/0.5/RPMS/el6/i386/>`_ 找到。

用户可以使用如下命令在虚拟机内安装 OSManager RPM 包， ::

  rpm -ivh http://dl.luoyun.co/LuoYunCloud/0.5/RPMS/el6/i386/luoyuncloud-osm-0.5-8.el6.i386.rpm


32位的 OSManager RPM 包在64位 CentOS6 操作系统中也可以安装。但其正常运行需要操作系统安装有32位的 glibc（glibc.i686）。

OSManager RPM 包安装完成之后，运行下面命令将 OSManager 设置为自动启动， ::

  /LuoYun/install.sh	

OSManager 中的 lyweb 需要用户提供一些关于虚拟机内应用软件的信息才可以正常工作。

 1. 首先用户需要编辑下面文件，来提供应用的版本信息， ::

      vi /LuoYun/build/VERSION
      
    该文件的格式如下例 ::

      [root@localhost ~]# cat /LuoYun/build/VERSION
      Appliance: 0.5.0
      CentosBase32: 6.3
      [root@localhost ~]#

    用户需要在上述文件的第二行，按格式要求，提供虚拟机内应用软件的名称及版本。

 #. 用户还需要编辑在下面目录中的 HTML 文件，来提供应用的详细信息 ::

      /LuoYun/custom/www/

OSManager 的 “/LuoYun/osmanager.sh” 是 OSManager 的入口脚本程序。如果用户对虚拟机内应用软件的启动有特殊要求，也可以选择修改该脚本。

至此, OSMananger 在 CentOS6 上的安装完毕。

将虚拟机制作成应用
----------------------------------------

因为虚拟机制作成为应用之后会其他用户使用，在制作应用之前需要对虚拟机做一些清理。 ::

  rm /etc/udev/rules.d/70*
  rm /etc/ssh/*key*
  rm -rf /tmp/*
  rm -rf /var/tmp/*
  find /var/log /etc/httpd/logs/ -type f -exec truncate -s0 {} \;
  rm /LuoYun/log/*
  rm -rf var/cache/*
  rm -f root/.bash_history


然后，将虚拟机关机。将虚拟机对应的虚拟磁盘用 "gzip" 命令压缩，通过 LuoYunCloud 的 Web 页面上载该压缩文件，就可以在 LuoYunCloud 平台上使用了。


为方便其他用户对应用的理解，建议在应用的压缩文件上载完毕后，在 LuoYunCloud 平台上对该应用做简单的说明并赋予标志性的 Logo。
