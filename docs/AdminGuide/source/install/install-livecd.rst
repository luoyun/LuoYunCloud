
使用 LiveCD 安装
============================
.. note::

   安装 Live CD 之前请先检查计算机是否支持虚拟化。您可以用 root 用户运行 LiveCD 里的如下命令进行检查 ::

     # /opt/LuoYun/bin/check

1. 安装 LiveCD

   a. 从 LiveCD 启动计算机,自动登陆系统 
      
      .. image:: /images/install/install-livecd-1.png
	 :width: 600
	 :target: ../_images/install-livecd-1.png

   #. 点击【硬盘安装】
      
      .. image:: /images/install/install-livecd-2.png
	 :width: 600
	 :target: ../_images/install-livecd-2.png

   #. 点击【下一步】 

      .. image:: /images/install/install-livecd-3.png
	 :width: 600
	 :target: ../_images/install-livecd-3.png

   #. 选择默认“美国英语式”，点击【下一步】  
      
      .. image:: /images/install/install-livecd-4.png
	 :width: 600
	 :target: ../_images/install-livecd-4.png

   #. 选择默认“基本存储设备”，点击【下一步】 
      
      .. image:: /images/install/install-livecd-5.png
	 :width: 600
	 :target: ../_images/install-livecd-5.png

   #. 选择“是，忽略所有数据”，点击【下一步】 

      .. image:: /images/install/install-livecd-6.png
	 :width: 600
	 :target: ../_images/install-livecd-6.png

   #. 自定义主机名称或默认，点击【下一步】 

      .. image:: /images/install/install-livecd-7.png
	 :width: 600
	 :target: ../_images/install-livecd-7.png

   #. 选择默认“亚洲/上海”，点击【下一步】

      .. image:: /images/install/install-livecd-8.png
	 :width: 600
	 :target: ../_images/install-livecd-8.png

   #. 自定义输入”根密码“并”确认“填写”，点击【下一步】 

      .. image:: /images/install/install-livecd-9.png
	 :width: 600
	 :target: ../_images/install-livecd-9.png

   #. 如果您的密码设置过于简单,会出现弹出框，继续使用该密码，点击【无论如何都使用】，点击【取消】重设密码 

      .. image:: /images/install/install-livecd-10.png
	 :width: 600
	 :target: ../_images/install-livecd-10.png

   #. 选择“使用所有空间”，点击【下一步】

      .. image:: /images/install/install-livecd-11.png
	 :width: 600
	 :target: ../_images/install-livecd-11.png

   #. 出现弹出框，点击【将修改写入磁盘】 
      
      .. image:: /images/install/install-livecd-12.png
	 :width: 600
	 :target: ../_images/install-livecd-12.png

   #. 等待安装

      .. image:: /images/install/install-livecd-14.png
	 :width: 600
	 :target: ../_images/install-livecd-14.png

   #. 出现下图界面，表示您的 LiveCD 安装完成，点击【关闭】，重启计算机，进入 LuoYunCloud 系统。 

      .. image:: /images/install/install-livecd-15.png
	 :width: 600
	 :target: ../_images/install-livecd-15.png

#. 配置 LuoYunCloud

   .. note::

      【配置 LuoYunCloud】以及下面的【启动与停止 LuoYun 服务】，都需要 root 权限

   a. 初始化 LuoYunCloud

      请确认您已经在新安装的 LuoYunCloud 系统中，打开终端，运行初始化命令 
      ::

	# bash /opt/LuoYun/install/init-luoyuncloud.sh 

#. 启动与停止 LuoYun 服务
   
   启动 LuoYun
   ::

      # /opt/LuoYun/bin/start

   停止 LuoYun
   ::

     # /opt/LuoYun/bin/stop
      
#. 创建我的虚拟机

   a. 打开浏览器，在地址栏输入 127.0.0.1 并回车（按Enter 键）。
   #. 点击右上角【登陆】按钮，输入默认用户名：admin、密码：admin 登陆 
   #. 点击【应用库】中的 owncloud 应用 
   #. 点击【创建虚拟机】 
   #. “名字”“CPU个数”“内存（M）”“隐藏”，可以根据自身情况加以修改，修改完成，点击【Creat】 
   #. 点击 启动虚拟机 
   #. 启动完成，点击"IP地址“ 

      .. image:: /images/install/start_instance.png
	 :width: 600
	 :target: ../_images/install_instance.png

   #. 点击【进入 ownCloud 首页】进入虚拟机 

      .. image:: /images/install/view_instance.png
	 :width: 600
	 :target: ../_images/view_instance.png

   #. 输入用户名：admin、密码：luoyun 登陆 

      .. image:: /images/install/owncloud_login.png
	 :width: 600
	 :target: ../_images/owncloud_login.png
	 
   #. 已进入 owncloud 应用，可以开始应用了 

      .. image:: /images/install/owncloud_login2.png
	 :width: 600
	 :target: ../_images/owncloud_login2.png

   至此，您的第一台虚拟机，已创建完毕！ 
