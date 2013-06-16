
.. _nginx-faq:

FAQ
==================================

Nginx 是一款高效的 web server ， LuoYunCloud 的 web 模块默认使用 Nginx 作 Web Server 前端。本文主要讲解如何在 LuoYunCloud 生成环境中使用 Nginx 。并将使用中可能会遇到的问题作一个简单说明。


LuoYunCloud 中应用 Nginx 最常遇到的问题归纳


Nginx 日志报错： "24: Too many open files"
-------------------------------------------------------------------------

LuoYunCloud 通常运行在 GNU/Linux 系统下，nginx 程序所能打开的文件个数由系统限制。运行下面命令可以看到当前用户能打开的文件数限制，假设 nginx 程序由 http 用户启动，那么它的限制就是由 http 用户决定的： ::

  # su - http
  $ ulimit -Hn
  $ ulimit -Sn


默认上面输出应该是 1024 （这是标准的 GNU/Linux 系统限制），现在我们修改个这个限制。
 
 1. 在文件 /etc/sysctl.conf 中添加  ::
      
      fs.file-max = 70000

 #. 在文件 /etc/security/limits.conf 中添加 ::

      http       soft    nofile   10000
      http       hard    nofile  30000

    这里的 http 是运行 nginx 程序的用户名，如果你的不一样，请对应修改。

 #. 使系统设制生效 ::

     # sysctl -p

   
 #. 修改 nginx 配置 

   编辑 /etc/nginx/conf/nginx.conf 文件，加入 worker_rlimit_nofile 30000; ，重启 nginx 。 ::

     nginx -s reload

现在再查看下用户可打开文件数限制，应该是正确的了。
