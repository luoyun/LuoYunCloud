如何使用 Filezilla 上传文件到虚拟机
======================================

本手册针对 Windows 用户使用习惯，介绍如何通过 sftp 上传/下载
LuoYunCloud 平台中虚拟机的文件。

注意：本文适用于任何开通 ssh ( 通常 sftp 一并开通了 ) 的 Linux 机器文件管理。


1. 请到 https://filezilla-project.org/ 下载 filezilla

   .. image:: /images/user/filezilla/Screenshot.png

2. 下载下面的 Windows 软件包

   .. image:: /images/user/filezilla/Screenshot-1.png

3. 出现如下下载页面，如果长时间没有动静，请注意一些提示信息

   .. image:: /images/user/filezilla/Screenshot-2.png
	  :width: 600

4. 下载完成后，安装好 filezilla, 打开它

   主机，请注意填写 "sftp://" 前线缀，端口和密码都是您的 ssh 访问配置。

   .. image:: /images/user/filezilla/Screenshot-3.png
	  :width: 600

5. 连接上 sftp 服务器后，就可以做类似 ftp 的操作了

   .. image:: /images/user/filezilla/Screenshot-4.png
	  :width: 600
