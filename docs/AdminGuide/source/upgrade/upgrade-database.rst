升级数据库
======================================

安装好 0.5 的 web 程序

SQLAlchemy 使用 alembic 自动升级数据表
----------------------------------------------------------
1. 生成自动更新数据

   下载 http://dl.luoyun.co/LuoYunCloud/0.5/alembic 保存到 /opt/LuoYun/web/tool/ 目录.进入 /opt/LuoYun/web/ 目录,执行: ::

     python ./tool/alembic revision --autogenerate -m 'Update 0.4 to 0.5'
   
   在 ./alembic/versions 目录下会产生一个类似 49b413bf73c9_update_0_4_to_0_5.py的文件.

#. 生成 offline SQL 文件

   上面命令生成的文件名中有 "49b413bf73c9",此处我们可以运行下面命令产生一个 SQL 文件. ::

     python ./tool/alembic upgrade 49b413bf73c9 --sql > ./4to5.sql

#. 更新数据库

   上面命令生成的4to5.sql文件,您可以查看其中内容.现在运行下面命令更新数据库: ::

     # su - postgres
     $ psql -d luoyun -U luoyun -f /opt/LuoYun/web/4to5.sql

   
   
