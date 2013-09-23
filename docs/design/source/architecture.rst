=====================
LYC 架构设计
=====================

LYC 的整体架构如下：

.. image:: images/lyc_arch.png


LYWEB
--------

1. lyweb 处理用户/管理员请求，与DB交互
2. lyweb 选择到哪个 lyclc 执行任务


LYCLC
--------

1. lyclc 处于监听模式，处理 lyweb, lynode 的请求
2. lyclc 选择到哪个 lynode 执行任务

LYNODE
---------

1. lynode 向 lyclc 注册自己
2. lynode 监控 lyosm, 自身系统运行状态

LYOSM
----------

1. lyosm 向 lynode 报告状态
