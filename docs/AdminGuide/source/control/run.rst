
运行 LuoYunCloud
---------------------------------

**运行／停止 LuoYunCloud 系统，需要管理员对整个系统有一定的了解。以免错误的操作影响系统的正常运行。**

单机情况下 LuoYunCloud 的运行步骤如下，如果 lyweb, lyclc, lynode 部署在不同机器上，请在相应机器上执行对应的启动命令即可：

1. 启动 postgresql

   对于lyweb、lyclc 这是最先需要启动的服务postgresql ::

     service postgresql start

#. 启动 lyweb

   postgresql 必须己经启动。 ::

     service lyweb start

   .. note::
      手动启动 lyweb 方法 ::

	python /opt/LuoYun/web/site.py >> /opt/LuoYun/logs/luoyun.tornado.log 2>&1 &


#. 启动 lyclc

   postgresql 必须己经启动。 ::

     service lyclc start

   .. note::
      手动启动 lyclc 方法 ::

	/opt/LuoYun/platform/bin/lyclc -d

#. 启动 lynode

   libvirtd、lyclc 必须己经启动。 ::

     service lynode start

   .. note::
      手动启动 lynode 方法 ::

	/opt/LuoYun/platform/bin/lynode -d

   
     
   

   

   


     
