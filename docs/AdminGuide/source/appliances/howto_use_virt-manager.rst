如何使用 virt-manager
=========================

virt-manager 是 libvirtd 的虚拟机管理前端，可以用来创建，删除，配置虚拟
机。也可以远程连接其他机器的 libvirtd ， 进而达到控制该机器的虚拟机目的。


virt-manager 管理远程机器
--------------------------

本节主要介绍，如何使用 LuoYunCloud LiveCD 里的 virt-manager 远程机器。

有很多用户使用的办工环境是 Windows ， 管理 LuoYunCloud 的计算节点，或者
利用其创建新的 LuoYunCloud 应用，都是很不方便的。我们的 LuoYunCloud
LiveCD 里己经有了 virt-manager 软件， 用户可以通过在本机创建一个虚拟机，
无论是 Virtualbox , VMware , Hyper-V 等创建的都可以， 从 LiveCD 引导虚
拟机，按照下面的流程，都可以连接到一台运行着 libvirtd 的服务器 (
LuoYunCloud 计算节点就可以 )。进行制作应用的工作。

1. 使用 Virtualbox 创建 LuoYunCloud 虚拟机

   打开 Virtualbox 软件，如下图：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot.png
	  :width: 600

   点击“新建”按钮, 出现新建虚拟机窗口：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-1.png

   填写或选择基本配置：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-2.png

   内存建议 1024M ：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-3.png

   新建一个磁盘：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-4.png

   新建磁盘向导：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-5.png
	  :width: 600

   使用动态分配磁盘：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-6.png
	  :width: 600

   指定磁盘大小：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-7.png
	  :width: 600

   完成磁盘创建：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-8.png
	  :width: 600

   完成虚拟机创建：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-9.png
	  :width: 600

   列表中可以看到新建的 LuoYunCloud 虚拟机：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-10.png
	  :width: 600

   选中 LuoYunCloud Demo 虚拟机，点击“设置”， 配置光盘指向 LuoYunCloud Live CD ISO 位置：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-11.png

   完成虚拟机设置，启动虚拟机，会看到 LuoYunCloud LiveCD 启动画面：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-13.png

   启动进入 LiveCD 系统的样子：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-14.png
	  :width: 600

2. 使用 virt-manager 软件连接远程的 libvirtd ( 虚拟机管理 )

   打开终端：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-15.png

   切换到 root 用户，运行 virt-manager 命令。这里要注意： 我们的
   LuoYunCloud LiveCD 0.5 版本需要安装一个软件包才能使用 virt-manager
   连接远程机器。使用 root 权限安装软件 ::

	 # yum install openssh-askpass

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-16.png

   出现下的错误，不用管它：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-17.png

   在 virt-manager 里的 "文件" 菜单，打开 "Add Connection" , 填上 root ssh 访问机器的配置：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-18.png

   输入 YES 和 root 密码：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-19.png

   稍作等待，就能连上远程的虚拟机管理了：

   .. image:: /images/appliances/howto_use_virt-manager/Screenshot-20.png

   接下来，请参考我们手册其他部分，利用 virt-manager 做其能做到的事情吧 。


FAQ
----------

1. 我是苹果电脑，没有 Ctrl+Alt+Delete 组合键怎么办？

   比如远程管理 Windows 2003 虚拟机，一登录就需要按 Ctrl+Alt+Delete 键。
   请看下图， virt-manager 菜单里有“发送按键”

   .. image:: /images/appliances/howto_use_virt-manager/send_keys.png
	  :width: 600

