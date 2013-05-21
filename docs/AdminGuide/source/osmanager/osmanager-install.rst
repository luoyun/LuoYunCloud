Windows 下安装
=========================

Windows XP 下安装
-----------------------------------

**前提条件**

首先在 windows XP 虚拟机上安装 python version 2.7

下载 python_

.. _python: http://python.org/

下载 `win-osmanager.zip`_ ,解压到 C 盘,如下图：

.. _`win-osmanager.zip`:  http://dl.luoyun.co/LuoYunCloud/0.5/soft/

.. image:: /images/osmanager/xp1.png
   :width: 600
   :target: ../_images/xp1.png

1. 将 win-osmanager 中的 lyosm.py 文件加载到系统启动项中，步骤：
打开我的电脑->控制版面->性能维护->任务计划(如下图)->

  .. image:: /images/osmanager/xp2.png
     :width: 600
     :target: ../_images/xp2.png

  点击添加任务计划，选择 win-osmanager文件夹中的 \LuoYun\bin\pyosm\lyosm.py 文件->选择计算机启动时->

  .. image:: /images/osmanager/xp3.png
     :width: 600
     :target: ../_images/xp3.png

  输入计算机密码->
  
  .. image:: /images/osmanager/xp4.png
     :width: 600
     :target: ../_images/xp4.png

  完成

  .. image:: /images/osmanager/xp5.png
     :width: 600
     :target: ../_images/xp5.png

2. 打开我的电脑->控制面板->安全中心，点击 Windows 防火墙 ，将防火墙设置为禁用状态，如下图：

  .. image:: /images/osmanager/xp6.png
     :width: 600
     :target: ../_images/xp6.png


**现​在​ Windows XP 应​用​的​ OsManager 服​务​已​经​配​置​完​成​，您​可​以​继​续​完​成​ LuoYunCloud 应​用​制​作​的​其​他​步​骤​（比​如​,用​gzip的​压​缩​镜​像​）**
