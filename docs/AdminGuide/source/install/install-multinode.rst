
多节点安装部署
==================
.. note::
   首先，确保单机部署的 LuoYunCloud 正常运行(参见 :ref:`install-yum`)。之后，在每台节点服务器（包括已经做为单机运行的节点），做如下配置和安装工作。以下说明假设节点服务器已经成功安装并运行 CentOS6 或是 RHEL6 Linux 操作系统。


配置节点网络为桥街模式
---------------------------
首先运行下面的命令安装 bridge-utils 软件包 ::

  yum install bridge-utils

进入 /etc/sysconfig/network-scripts 目录 ::

  cd /etc/sysconfig/network-scripts

编辑 /etc/sysconfig/network-scripts/ifcfg-eth0 文件。如果该文件不存在，请确认 NetworkManager 处于关闭状态。然后，将 eth0 连接至 br0  ::

  DEVICE=eth0
  ONBOOT=yes
  BRIDGE=br0

在此目录下新建 br0 的配置文件，/etc/sysconfig/network-scripts/ifcfg-br0，并将原先属于 eth0 的 IP，配置给新建的 br0 。例如  ::

  DEVICE="br0" 
  ONBOOT=yes
  TYPE=Bridge
  BOOTPROTO=none
  IPADDR=192.168.1.2
  GATEWAY=192.168.1.1
  NETMASK=255.255.255.0
  DELAY=0

重启 network 服务即可 ::

  service network restart



安装并配置 lynode 节点服务程序
--------------------------------------

确定节点服务程序已经安装。新增加的节点可以使用如下命令安装节点服务程序 ::

  # wget http://dl.luoyun.co/LuoYunCloud/0.5/RPMS/el6/x86_64/luoyuncloud.repo 
  # mv luoyuncloud.repo /etc/yum.repos.d/luoyuncloud.repo
  # yum install luoyuncloud-node

然后修改 lynode 的配置文件 lynode.conf  ::

  vi /opt/LuoYun/platform/etc/luoyun-cloud/lynode.conf

- 指定 lynode 与 lyclc 的连接方式，以及 lyclc 的 IP 地址。下述中的“192.168.1.1” IP 地址需换成用户所部署的 lyclc 的 IP 地址 ::

    LYCLC_AUTO_CONNECT = DISABLE
    LYCLC_HOST = 192.168.1.1
    LYCLC_PORT = 1369

- 指定网络连接方式 ::

    LYNODE_NET_PRIMARY = br0

保存后，重启 lynode 服务。lynode 会自动连接 lyclc 并注册 ::

  service lynode restart

           
最后，需要登录管理后台，进入节点标签，勾选新加入的节点。



部署完成后的注意事项
--------------------------

- 在原单机部署时使用的虚拟机器，在平台转为多点部署后，需要修改/opt/LuoYun/platform/etc/luoyun-cloud/lynode.sysconf，只需修改LYCLC_HOST ::

    LYCLC_HOST = 192.168.122.1  #此处请改为新设置的IP地址
    LYCLC_PORT = 1369 #此处不要修改
    LYNODE_TAG = 3 #此处为节点在数据库中的编号，不要修改
    LYNODE_SECRET = a91f69e3-950b-4977-9ea1-bc0f50154a0e #此处为节点注册密码，不要修改

  然后，将原先创建的虚拟机重启，即可在多节点环境的LuoYunCloud平台上正常使用。


- 确定多点部署成功完成后，可以将节点服务器的操作系统设置为不启动图形界面，这样可以节省一部分计算资源供云平台使用

  编辑 /etc/inittab 文件。找到 id:5: initdefault: 这一行，将它改为 id:3:initdefault: 后重新启动系统即可
