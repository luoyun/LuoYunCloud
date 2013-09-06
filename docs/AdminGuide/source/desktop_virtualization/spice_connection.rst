如何使用 spice 客户端连接 LuoYunCloud 远程桌面?
======================================================

一、 下载 LuoYunCloud 
------------------------------

LuoYunCloud 下载地址： `http://luoyun.co/downloads`_

.. _http://luoyun.co/downloads: http://luoyun.co/downloads

二、 安装LuoYunCloud 
------------------------------

从 LiveCD 安装： `http://dl.luoyun.co/AdminGuide/install/install-livecd.html`_

.. _http://dl.luoyun.co/AdminGuide/install/install-livecd.html: http://dl.luoyun.co/AdminGuide/install/install-livecd.html

三、 使用 spice 客户端连接 LuoYunCloud 远程桌面 
---------------------------------------------------

假设安装好 LuoYunCloud 软件的服务器 IP 为 192.168.1.15 ,选择所需应用后创建虚拟机并开机，【Base Information】中【远程桌面】选项会有一个端口号假设为：5902 

.. image:: /images/desktop_virtualization/1.png
      :target: ../_images/1.png

Windows
~~~~~~~~~~~~~~~

1.下载 `virt-viewer`_

.. _virt-viewer:  http://dl.luoyun.co/win-soft/virt-viewer-x86-0.5.6.msi

2.安装 virt-viewer 程序完毕，用户在 Windows 开始菜单找到 VirtViewer , 打开 Remote Viewer 

.. image:: /images/desktop_virtualization/2.png
      :target: ../_images/2.png

3.用户填写链接参数， 如： spice://192.168.1.15:5902 

.. image:: /images/desktop_virtualization/3.png
      :target: ../_images/3.png

4.如若连接正确，会出现验证画面

.. image:: /images/desktop_virtualization/4.png
      :target: ../_images/4.png

5.输入默认密码，如 luoyun, 出现虚拟机画面 

.. image:: /images/desktop_virtualization/5.png
      :width: 600
      :target: ../_images/5.png


Linux
~~~~~~~~~~~~~~

1.下载安装 spice 
命令行执行命令: ::

sudo apt-get install spice-client-gtk

2.终端输入“spicy”,如图：

.. image:: /images/desktop_virtualization/6.png
      :target: ../_images/6.png

3.用户填写链接参数

.. image:: /images/desktop_virtualization/7.png
      :target: ../_images/7.png


4.如若链接正确，会出现验证画面 

.. image:: /images/desktop_virtualization/8.png
      :target: ../_images/8.png

5.输入默认密码，如 luoyun, 出现虚拟机画面 

.. image:: /images/desktop_virtualization/9.png
      :width: 600
      :target: ../_images/9.png
