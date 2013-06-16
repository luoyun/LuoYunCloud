从 0.4 升级到 0.5 注意事项
------------------------------------

.. warning::

   0.5 的升级涉及到数据库的更新,请先使用 postgres 用户备份当前数据库. ::

     # su - postgres
     $ pg_dump luoyun > luoyun-backup-20121121.sql
     $ pwd
     /var/lib/pgsql

   我们示例是将数据库备份为 /var/lib/pgsql/luoyun-backup-20121121.sql 文件.请保管好这个文件,今后如果有需要可以用这个文件恢复数据库: ::

       # su - postgres
       $ dropdb luoyun
       $ createdb luoyun -O luoyun
       $ psql -d luoyun -U luoyun -f luoyun-backup-20121121.sql

.. note::
   请同时保存好这些数据,以防止升级中操作错误,影响生产环境:

   - Appliance 数据,默认存在 /opt/LuoYun/data/

   - 旧的 lyclc, lynode 配置文件,默认存在 /opt/LuoYun/platform/etc/luoyun-cloud/

   - 旧的 web 目录,默认存在 /opt/LuoYun/web/.这里有 user 等静态文件.

   - nginx 配置文件,　默认在 /etc/nginx/



