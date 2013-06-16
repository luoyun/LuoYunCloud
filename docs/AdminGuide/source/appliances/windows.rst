制作 Windows 应用
====================

本文以 Windows XP 系统为例，介绍如何制作一个能在 LuoYunCloud 平台上运行的应用。

**注意** ： 0.5 的开发版中己经默认支持 spice 远程显示协议，因此我们的
Windows XP 应用也会默认加上 spice 协议支持（主要是驱动）

我们以 LuoYunCloud 0.5 LiveCD 安装后的系统为例，前提 : 

1. 安装好  LuoYunCloud LiveCD 系统
2. 以下使用本机的 virt-manager 创建虚拟机
3. 本地准备好 xp.iso ( Windows XP 的映像，支持正版 )， 并保存在 `/var/lib/libvirt/images/xp.iso`

你可以自由选择其他方式，或者用 qemu-kvm 命令创建虚拟机，或者用
virt-manager 远程连接服务器的方式创建虚拟机。


1. 启动 virt-manager 软件

   进入 LuoYunCloud LiveCD 安装好的系统，如下图所示，打开 **虚拟系统管理器** (即 virt-manager 软件)

   .. image:: /images/appliances/Screenshot.png

   如果出现类似下面的提示，请输入管理员 (root) 密码：

   .. image:: /images/appliances/Screenshot-1.png

   virt-manager 打开后，可能如下图所示（此处我的测试平台己有一些机器，
   你的平台可能不一样， **注意** : 以 "i-" 开头的默认是 LuoYunCloud 启
   动的虚拟机，请不要在此处操作，查看可以）

   .. image:: /images/appliances/Screenshot-2.png

2. 创建虚拟机

   点击创建虚拟机按钮，填写虚拟机名字：

   .. image:: /images/appliances/Screenshot-3.png

   选择我们的 iso 文件：

   .. image:: /images/appliances/Screenshot-4.png
   .. image:: /images/appliances/Screenshot-5.png

   配置 CPU, 内存 （这里和最终在云平台运行没有关系）：

   .. image:: /images/appliances/Screenshot-6.png

   指定磁盘大小（ 请尽量小点， 我们选择 6 G， 如果运行需要更多空间，可以通过数据盘扩充）：

   .. image:: /images/appliances/Screenshot-7.png

   生成新的虚拟机

   .. image:: /images/appliances/Screenshot-8.png

   安装 Windows XP 操作系统

   .. image:: /images/appliances/Screenshot-9.png
	  :width: 600
	  :target: ../_images/Screenshot-9.png

   安装完成，重启进入系统

   .. image:: /images/appliances/Screenshot-10.png
	  :width: 600
	  :target: ../_images/Screenshot-10.png

3. 安装 OSM 和 spice 驱动

   配置好虚拟机网络，打开 http://dl.luoyun.co/win-soft/ ， 下载 LuoYunCloud-OSM-1.0.exe , spice-guest-tools-0.3.exe 两个程序， 安装上

   .. image:: /images/appliances/Screenshot-11.png
	  :width: 600
	  :target: ../_images/Screenshot-11.png

   关机！

4. 制作应用并上传

   按照我们虚拟机命名，我们的磁盘文件是 `/var/lib/libvirt/images/Windows-test.img` ， 使用 gzip 压缩它 ::

	 gzip -c /var/lib/libvirt/images/Windows-test.img > /opt/LuoYun/windows-test.img.gz

   压缩会花一点时间（和磁盘大小有关），完成后，我们应用就制作好了。现在我们用命令上传这个应用 ::

	 python /opt/LuoYun/web/tool/upload-appliance.py /opt/LuoYun/windows-test.img.gz

5. 最后几步

   现在我们的 LuoYunCloud 平台己经有这个应用了， 使用这个应用，我们创建一个虚拟机，启动它，用 spice-client 连接上这个虚拟机，让系统找到硬件，自动更新驱动程序。

   .. image:: /images/appliances/Screenshot-12.png
	  :width: 600
	  :target: ../_images/Screenshot-12.png

   重启虚拟机，开机出现 cmd 窗口(如下图)，请不要关闭，它会自动结束：

   .. image:: /images/appliances/Screenshot-13.png
	  :width: 600
	  :target: ../_images/Screenshot-13.png


   如果 OSM 安装正确，系统托盘能看见一个图标：

   .. image:: /images/appliances/Screenshot-14.png

   现在查看 LuoYunCloud web 界面，能看到虚拟机己经正常运行了：

   .. image:: /images/appliances/Screenshot-15.png
	  :width: 600
	  :target: ../_images/Screenshot-15.png



FAQ
----------


1. OSM 没有运行怎么办？

   打开 cmd , 进入 OSM 安装目录，运行 osmwinserv.exe 程序， 如果出现 "系统无法执行指定的程序" 错误, 请下载 http://www.microsoft.com/zh-cn/download/details.aspx?id=5582 ， 安装后，删除 OSM 后重装即可。

   .. image:: /images/appliances/Screenshot-16.png
	  :target: ../_images/Screenshot-16.png
