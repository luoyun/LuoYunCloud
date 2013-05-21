lynode.conf配置文件说明
==============================================

**lynode.conf是lynode服务器的配置文件,通过此文件,您可以指定lynode的工作方式与一些技术细节.
默认安装时,此文件位于 /opt/LuoYun/platform/etc/luoyun-cloud 目录中.**

配置文件参数说明
----------------------------------------------
**以#开头的是开发人员编码时所做的注释,对紧接着下面的行所起的作用加以了注释说明,您可以通过注释帮助您了解此文件的功能.**

下面我们来逐项加以说明:

虚拟化模式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::
   
   # Configuration file for LuoYun cloud compute nodes
   #
   # Hypervisor driver used on compute node
   #
   # default is KVM
   #
   LYNODE_DRIVER = KVM

**此处的前6行是由#号表示的注释(下文中将不再引用注释)**

所注释的参数行是紧随其后的: LYNODE_DRIVER = KVM

此参数指明了lynode采用的虚拟化工作模式,默认采用的是KVM虚拟化方案,未来版本中还将提供Xen等其他虚拟化方案的支持.

指定lynode服务配置记录的保存路径
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_SYSCONF_PATH = /opt/LuoYun/platform/etc/luoyun-cloud/lynode.sysconf

此参数表示的是lynode服务器的配置在连接成功后生成的记录文件保存路径,默认与lynode.conf在同一目录,文件名为lynode.sysconf.如果需要重新配置node服务器,可以将lynode.sysconf文件删除,系统会在重新配置时自动生成该文件.

指定lynode服务器与lyclc服务器的连接方式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYCLC_AUTO_CONNECT = ALWAYS
   LYCLC_HOST = 
   LYCLC_PORT = 1369

此处的三行参数指定了lynode服务器与lyclc服务器的连接方式.

LYCLC_AUTO_CONNECT
 指定连接方式,默认为ALWAYS,表示lynode服务器将不断通过网络连接到lyclc服务器,可选参数还有ONCE,表示仅连接lyclc服务器一次,并在连接成功后记录lyclc服务器的ip地址,以后直接连接所记录的lyclc服务器ip地址,还可选DISABLE,表示通过第二行的参数连接.

LYCLC_HOST 
 指定lyclc服务器的IP地址,当第一参数为DISABLE时生效.默认为空.

LYCLC_PORT
 指定与lyclc服务器连接时所使用的端口号.


连接lyclc服务器的方式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYCLC_MCAST_IP = 228.0.0.1
   LYCLC_MCAST_PORT = 1369

此处的两行参数指定的是lynode服务器在尝试自动连接lyclc服务器时所使用的网络掩码与监听端口.

lynode服务器的数据存储位置
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_DATA_DIR = /opt/LuoYun/platform/node_data

此参数指定是用户最关心的数据存储问题,lynode服务器提供的服务数据都保存的此处指定的目录,默认为*/opt/LuoYun/platform/node_data* ,您也可以自定义到其他目录,但node投入使用后请不要轻易修改此参数,以免造成用户数据丢失. 在此参数指定的目录下将保存用户创建的虚拟机,额外存储的磁盘,以及应用等数据.请确保此目录空间足够使用.


UUID设置
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_UUID_PATH = /opt/LuoYun/platform/etc/luoyun-cloud/lynode.uuid


此参数为后续版本的高级设置保留,目前暂未使用.


指定lynode的日志记录位置
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_LOG_PATH = /opt/LuoYun/platform/logs/lynode.log

此参数指定lynode服务器的日志文件保存位置,默认为 /opt/LuoYun/platform/logs/lynode.log ,管理员可以查看此文件来了解lynode的运行情况.


PID设置
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_PID_PATH = /var/run/lynode.pid


此参数为后续版本的高级设置保留,目前暂未使用.

VM模板参数自定义
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   #LYNODE_VM_TEMPLATE =
   #LYNODE_VM_DISK_TEMPLATE =
   #LYNODE_VM_NET_BRIDGE_TEMPLATE =
   #LYNODE_VM_NET_NAT_TEMPLATE =

此处的四行参数默认被注释掉不启用,由于luoyuncloud推荐使用centos环境,不需要另行指定此参数值,但考虑到一些用户使用debain/ubuntu类系统,所以提供此处的参数供高级用户使用.

**如果您使用的是ubuntu服务器环境,可以去掉此行的第一行 #LYNODE_VM_TEMPLATE = 的 # 号,并在=号后指定自定义的模板xml文件路径.**

指定网络连接方式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_NET_PRIMARY = br0
   LYNODE_NET_SERCONDARY = 

此处的两行参数指定的是网卡的工作方式.单机部署时第一行参数建议改为virbr0,以免虚拟机无法获得IP地址.默认配置为br0,第二行参数指定的是第二块网卡的IP地址,默认为空.


osm的旧版读取方式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYOSM_CONF_PATH = /LuoYun/conf/luoyun.conf
   LYOSM_KEY_PATH = /LuoYun/conf/luoyun.key

此处的两行参数为0.2版的osmanger读取参数方式,目前已经停止使用,仅为保留.


lynode运行方式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_DAEMON = 1

此参数指定lynode服务程序的运行方式,默认为1,lynode服务程序以后台服务的形式运行;可选参数0,可指定lynode以非后台的形式运行.


调试模式开关
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   LYNODE_DEBUG = 0

此参数可指定lynode服务以调试模式运行,使lynode的日志文件记录更详细的内容,默认为0,不打开调试模式;可选参数1,打开调试模式.
