停止 LuoYunCloud
------------------------------
**运行／停止 LuoYunCloud 系统，需要管理员对整个系统有一定的了解。以免错误的操作影响系统的正常运行。**

.. note::
   如果要完全停止整个 LuoYunCloud ，请先在 LuoYunCloud Web 管理后台停止所有虚拟机器。如果仅要重启 LuoYunCloud 的部分模块，只需操作对应的模块即可，不需停止所有服务。

1. 停止 lyweb  ::

     service lyweb stop

   .. note::

      手动停止 lyweb 方法

      a. 查找 lyweb 程序的进程号 ::

	   # ps aux|grep lyweb
	   root      3036  1.0  0.0 103252   828 pts/2    S+   21:07   0:00 grep lyweb

	 上面 3036 处就是 lyweb 的进程号。

      #. 用 kill 杀掉此进程 ::

	   kill -9 3036


#. 停止 lyclc ::

     service lyclc stop
   
   .. note::
      手动停止 lyclc 方法

      a. 查找 lyclc 程序的进程号 ::

	   # ps aux | grep lyclc
	   root      4750  0.0  0.0 103300   888 pts/28   S+   21:11   0:00 grep lyclc
	   root     29487  0.0  0.1 194240 19968 ?        S    Nov23   2:04 /opt/LuoYun/platform/bin/lyclc -d

	 上面 29487 处就是 lyclc 的进程号。

      b. 用 kill 杀掉此进程 ::

	   kill -9 29487

#. 停止 lynode ::

     service lynode stop
     
   .. note::
      手动停止 lynode 方法


      a. 查找 lynode 程序的进程号 ::

	   # ps aux | grep -i 'bin/lynode'
	   root      4875  0.0  0.0 103300   904 pts/28   S+   21:15   0:00 grep -i bin/lynode
	   root     29542  0.0  0.0 2294152 12300 ?       S    Nov23  23:23 
	   /opt/LuoYun/platform/bin/lynode -d
	
	 上面 29542 处就是 lynode 的进程号。

      #. 用 kill 杀掉此进程 ::
	
	   kill -9 29542


     
	

      
