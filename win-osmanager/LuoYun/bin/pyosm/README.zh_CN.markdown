开发/编绎前提条件
==============

请先在 Windows 平台上安装下面程序:

 - [Python](http://www.python.org/)
 - [py2exe](http://www.py2exe.org/) (将 py 文件编绎成 exe)
 - [pywin32](http://sourceforge.net/projects/pywin32/) (pywin32 不是只有 32 位, 编写了 Windows 服务程序)
 - [wxPython](http://www.wxpython.org/) (编写了系统托盘)
 - [NSIS](http://nsis.sourceforge.net/) (打包成安装程序)



编绎 EXE 程序
===========

win-osmanager 使用 py2exe 编绎,　源码目录中的 winsetup.py 是编绎配置文件.

下截 win-osmanager 源码,进入目录,运行:

    winsetup.py py2exe

命令执行成功后,在当前目录下生成 build, dist 目录.　dist 目录中的文件就是生成的结果.



生成安装程序
==========

前提:

 - 编绎成 EXE 程序,　进入 dist 目录
 - 安装好 NSIS

满足前提条件,在 dist 目录可以看到 osminstall.nsi 文件(和 NSIS 同样图
标),右键选择编绎即可. 编绎成功后,会在当前目录生成 EXE 安装程序.



安装/删除 OSM Windows 服务
========================

osmwinserv.py 编绎后是 osmwinserv.exe 文件,　打开 Windows 系统的 CMD,
进入 osmwinserv.exe 所在的目录,定装服务:

    osmwinserv.exe -install -interactive -auto

参数解释:

 - `-install` 表示安装
 - `-interactive` 表示允许服务和 GUI 交互,即 OSM system tray (taskbaricon) 能出来
 - `-auto` 表示该服务在 Windows 系统启动时会自动启动

删除服务,运行:

    osmwinserv.exe -remove

**注意**: 如果您己生成了安装程序,就不用这里的手动安装服务步聚了,安装程
  序会自动做这些事情.