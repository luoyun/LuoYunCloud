=====================
Python API
=====================

参考：

1. `Python API bindings <http://libvirt.org/python.html>`_


本文学习 libvirt API 的 python binding 设计


Python binding 根据 API 的 xml 正式描述文件自动生成。围绕两个类
virConnect 和 virDomain 映射。

在 C API 中如下实现 ::

  int virConnectNumOfDomains (virConnectPtr conn);
  int virDomainSetMaxMemory (virDomainPtr domain, unsigned long memory);

在 Python 中变成 ::

  virConnect::numOfDomains(self)
  virDomain::setMaxMemory(self, memory)

这些 API 都是自动生成的，可以在源代码中的 libvirtclass.txt 文件中查看具体情况。

也有一些 api 没能自动映射到 C API 上：

- virConnectListDomains 使用 virConnect::listDomainsID(self) 替换， 返回
  当前运行的所有 domain 的 ID 列表.

- virDomainGetInfo 使用 virDomain::info() 替换， 返回：

  1. state: one of the state values (virDomainState)
  2. maxMemory: the maximum memory used by the domain
  3. memory: the current amount of memory used by the domain
  4. nbVirtCPU: the number of virtual CPU
  5. cpuTime: the time used by the domain in nanoseconds


示例

basic ::

  import libvirt
  import sys

  conn = libvirt.openReadOnly(None)
  if conn == None:
      print 'Failed to open connection to the hypervisor'
      sys.exit(1)

  try:
      dom0 = conn.lookupByName("Domain-0")
  except:
      print 'Failed to find the main domain'
      sys.exit(1)

  print "Domain 0: id %d running %s" % (dom0.ID(), dom0.OSType())
  print dom0.info()

