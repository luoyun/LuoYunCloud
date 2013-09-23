=====================
libvirt API 基本概念
=====================

参考：

1. `The libvirt API concepts <http://libvirt.org/api.html>`_


本文学习 libvirt API 的设计理念


对象开放 ( Objects Exposed )
-----------------------------------

libvirt 的目标就是为管理 hypervisor 实现的系统环境提供接口。

.. image:: images/libvirt-object-model.png

上面的图片显示了几种主要的接口：

- virConnectPtr

  表示到一个 hypervisor 的连接， 使用一种 virConnectOpen 接口可以获得连接.

- virDomainPtr

  表示一个 active 或 defined 的 domain , 使用 virConnectListAllDomains
  可以列出一个 hypervisor 的所有 domain.

- virNetworkPtr

  表示一个 active 或 defined 的 network , 使用
  virConnectListAllNetworks 可以列出一个 hypervisor 的所有虚拟化
  network

- virStorageVolPtr

  表示一个可以被 domain 使用的 storage volume ( as a block device ), 为
  virStorageVolLookupByPath 提供 path 值可以获得 storage volume object
  .

- virStoragePoolPtr

  表示一个 storage pool , virConnectListAllStoragePools 可以列出
  hypervisor 上所有 storage pool , 为 virStoragePoolLookupByVolume 指定
  storage volume , 可以得到 storage pool .



函数和一些命名 ( Functions and Naming Conventions )
---------------------------------------------------------


- Lookup [...LookupBy...]

  使用一些标记查找一个对象，如：

  - virDomainLookupByID
  - virDomainLookupByName
  - virDomainLookupByUUID
  - virDomainLookupByUUIDString

- Enumeration [virConnectList..., virConnectNumOf...]

  获取一个 hypervisor 的一系列信息，如：

  - virConnectListDomains
  - virConnectNumOfDomains
  - virConnectListNetworks
  - virConnectListStoragePools

- Description [...GetInfo] 

  获取一个对象的基本信息， 如：

  - virNodeGetInfo
  - virDomainGetInfo
  - virStoragePoolGetInfo
  - virStorageVolGetInfo

- Accessors [...Get..., ...Set...]

  查询或设置对象的属性， 如：

  - virConnectGetType
  - virDomainGetMaxMemory
  - virDomainSetMemory
  - virDomainGetVcpus
  - virStoragePoolSetAutostart
  - virNetworkGetBridgeName

- Creation [...Create, ...CreateXML]

  创建和运行对象， xxxCreateXML api 可以基于 XML 描述创建对象。 xxxCreate api 可以基于己有的对象创建对象：

  - virDomainCreate
  - virDomainCreateXML
  - virNetworkCreate
  - virNetworkCreateXML

- Destruction [...Destroy]

  关闭、禁止、删除对象，如：

  - virDomainDestroy
  - virNetworkDestroy
  - virStoragePoolDestroy



The libvirt Drivers
------------------------

.. image:: images/libvirt-driver-arch.png



Daemon and Remote Access
-----------------------------

.. image:: images/libvirt-daemon-arch.png
