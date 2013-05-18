配置邮件服务
----------------------------

配置 LuoYunCloud 的发信服务

1. 安装配置 Postfix

   默认安装好的 Postfix 就可以发送邮件了,在 web 服务所在的节点上,安装并启动 Postfix: ::

     # yum install postfix
     # service postfix start

#. 配置 LuoYunCloud web

   配置 /opt/LuoYun/web/luoyun.cfg 文件中 email 信息: ::

     [email]

     name = LuoYunCloud Admin
     from = noreply@luoyuncloud.com

     smtp_server = localhost
     smtp_port = 25
