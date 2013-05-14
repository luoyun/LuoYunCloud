LuoYunCloud 发布以来，收到很多用户的问题以及建议，我们非常感谢！为了减省用户的时间，我们将一些常问问题整理后，放在这里，欢迎大家查阅！

Live CD 可以不安装直接运行吗？
===============================================

**理论上是可以的，但为了用户能全面体验 LuoYunCloud 平台，我们目前不支持这样做！**

因为我们的 LiveCD 自带了一个 ownCloud 演示应用，默认需要 3Ｇ 磁盘空间，加上 LiveCD 自己的 1Ｇ 多磁盘空间。而为了能适应更多不同规格的机器，LiveCD 磁盘默认用的 4G 大小（这也是 RHEL/CentOS/Fedora 等 LiveCD 的默认做法）。因此，在 LiveCD 中不能演示 ownCloud 应用，也就不能体会 LuoYunCloud 的全部功能。


为什么创建虚拟机只能配置 256M 内存，1CPU ？
================================================================================

**LuoYunCloud 的虚拟机资源没有任何限制！**

默认 LuoYunCloud 系统里，每个用户缺省资源配置如下，在配置文件 /opt/LuoYun/web/settings.py 中： ::
  
  USER_DEFAULT_MEMORY = 256    # 256M 内存
  USER_DEFAULT_CPUS = 1        # 1 CPU
  USER_DEFAULT_INSTANCES = 10  # 10 虚拟机创建许可
  USER_DEFAULT_STORAGE = 2     # 2 G 附加存储


您可以修改这个配置，重启 LuoYunCloud 即可。我们下个版本会将这个配置编辑放到管理界面。

**对于已经存在的用户，请通过 Web 管理界面，点击"用户”管理，找到指定用户，编辑资源配置即可。**


管理界面配置用户资源时有限制怎么办？
===================================================================

**这个限制是为了保护系统。默认限制：内存小于 10240M、CPU 小于 20个、虚拟机小于 100个、附加存储小于 100G。**

目前版本写在程序内部，下一版本会在管理界面配置。如有需求，请修改 /opt/LuoYun/web/app/admin/forms.py 里下面的配置数字即可： ::

  class UserResourceForm(Form):
    memory = IntegerField( _('Memory(M)'), [validators.NumberRange(min=256, max=10240)])
    cpus = IntegerField( _('CPUs'), [validators.NumberRange(min=1, max=20)])
    instances = IntegerField( _('Instances'), [validators.NumberRange(min=1, max=100)])
    storage = IntegerField( _('Storage(G)'), [validators.NumberRange(min=2, max=100)])


我的系统能跑多少个虚拟机？
==========================================================

**可以跑很多！**

目前 LuoYunCloud 基于 KVM 虚拟化，运行的虚拟机个数取决于您的物理机资源。另外，我们控制节点的配置文件中有个全局因子，控制云平台运行虚拟化级别： ::

  云平台可以运行的虚拟机总数 = 全局因子 x 所有计算节点的CPU总核数

以 www.LuoYunCloud.com 演示平台为例，我们一共有 3 台服务器，配置如下： 

  1. 16G 内存

  2. 1颗 4 核 CPU ( Intel(R) Xeon(R) CPU E5606 @ 2.13GH )

  3. 1T 硬盘

目前跑了 123 个虚拟机，使用 32 Ｇ内存。

.. image:: /images/FAQ/luoyuncloud-admin.png



节点注册不上？
===========================================

节点注册不上， 可以按下面步骤检查:

 1. 检查 iptables（防火墙）

    首先，确定 lyclc ( LuoYunCloud 控制节点） 所在的 iptables（防火墙）打开了如下端口。确定文件 /etc/sysconfig/iptables 包含以下内容。 ::

      -A INPUT -p tcp -m tcp --dport 1369 -j ACCEPT

    以上内容要在下面规则之前： ::

      -A INPUT -j REJECT --reject-with icmp-host-prohibited

 #. 检查 LuoYunCloud web 管理后台是否启用节点

    确保下图中的 可用 是勾选的。

    .. image:: /images/FAQ/node-enable.png


访问不了虚拟机的 Web 页面？
===================================================
可以按下面步骤检查:

 1. 检查 iptables（防火墙）

    查看需要访问的 web 端口是否开放。比如 80, 8080, 8001 。

 2. 检查 nginx 的错误日志

    默认情况下， nginx 错误日志位于 /var/log/nginx/error.log 。关于 nginx 更多的错误处理请看 :ref:`nginx-faq` 中错误处理。
    

