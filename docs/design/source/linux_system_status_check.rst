GNU/Linux 系统状态检查
===========================

proc 文件系统下的实时信息
-------------------------

- /proc/meminfo 内存
- /proc/cpuinfo CPU
- /proc/loadavg 负载

  一个 **/proc/loadavg** 文件内容示例::

  0.06 0.17 0.30 1/478 6043

  **0.06 0.17 0.30** 表示系统在 1 , 5, 15 分钟内 loadavg 值，　
  **1/478** 表示 "**当前运行进程数/总进程数**" ， **6043** 表示最近运行
  的进程 ID 号。

  **loadavg** 表示当前系统有多少个处于 running 状态或 uninterupt
  sleeping 状态的平均进程个数。一般来说处于不可中断的睡眠状态是指进程等
  待 io 时。当一个进程需要读入磁盘数据时，系统就会将其置为不可中断的睡
  眠，一直等到数据到来，这个时期进程虽然不显示占用cpu，但是操作系统的磁
  盘调度相应的部分以及所需外围设备的操作都应该记入该进程。所以处于这个
  状态的进程也被记入 loadavg 中。处于这个状态的进程是没有办法杀死的。

  被计入 loadavg 的进程并不一定占用了很高的 CPU ，　所以 loadavg 与
  CPU 没有一定的对应关系。

  衡量操作系统当前负载情况，需要结合 loadavg 和 CPU 利用率。

  参考：

  - http://www.unixresources.net/linux/clf/newbie/archive/00/00/46/84/468436.html
  - http://www.centos.org/docs/5/html/5.2/Deployment_Guide/s2-proc-loadavg.html

- /proc/uptime 系统运行时间
- /proc/net/dev 网卡
