Sphinx 简介
==============

资源
----

- `项目主页 <http://sphinx-doc.org/>`_
- 中文资源

  - `中文入门 <http://sphinx-doc-zh.readthedocs.org/en/latest/tutorial.html>`_
  - `Sphinx 中文文档 <http://sphinx-doc-zh.readthedocs.org/en/latest/contents.html>`_
  - `可爱的reStructuredText <http://wiki.jerrypeng.me/rest-tjlug/>`_

- 英文资源

  - `Read the Docs <https://readthedocs.org/>`_
  - `reStructuredText Markup Specification (英文详细手册） <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html>`_


使用
----

1. 创建项目::

   $ sphinx-quickstart

2. 编辑 source 下的 index.rst

3. 输出　html 格式::

   $ make html


生成 PDF 文件
-----------------

先将 rst 格式输出为 tex 格式,再用　tex 工具输出 PDF 的. 默认的 ``make
latexpdf`` 不能正确处理中文.

1. 配置 conf.py 文件::

	 latex_elements = {
	 'preamble': '''
	 \usepackage{xeCJK}
	 \setCJKmainfont[BoldFont=SimHei, ItalicFont=Microsoft YaHei]{Microsoft YaHei}
	 \setCJKmonofont[Scale=0.9]{Droid Sans Mono}
	 \setCJKfamilyfont{song}[BoldFont=SimSun]{SimSun}
	 \setCJKfamilyfont{sf}[BoldFont=SimSun]{SimSun}
	 ''',
	 }

1. 运行 ``make latex`` 生成 tex 文件
2. 进入 **build/latex** 目录,　运行 ``xelatex XXXX.tex`` 生成 PDF 文件


中文
------

设置 conf.py 的 ``language = 'zh_CN'``


主题
-----

- `<http://sphinx-doc.org/theming.html>`_

一些主题:

- `cloud_sptheme <https://pypi.python.org/pypi/cloud_sptheme>`_
