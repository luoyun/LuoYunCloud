===========================
LuoYunCloud API 基本设计
===========================

API 提供自定程序与 LuoYunCloud 进行交互。基本设计原则如下：


1. 所有请求，发起就是 k-v 值, 如需验证，就要带一个 session_key 一类的值。
2. 返回都是 JSON ::

     {
         code: Number,  # 返回状态
         desc: string,  # 返回状态的补充描述
         其他数据,
     }

一个 Python API 请求示例 ( t_post.py ) ::

  #!/usr/bin/env python 
  # _*_ coding: utf-8 _*_ 

  import base64 
  import urllib 
  import httplib 
 

  username = 'luoyun'
  password = 'luoyun'
  host = '127.0.0.1'

  params = urllib.urlencode({'username': username, 'password': password})
  auth = base64.b64encode('cleartext username'+ ':'+ 'cleartext passwords') 
  headers = { "Authorization": "Basic "+ auth,
              'Content-Type': 'application/x-www-form-urlencoded',
              'User-Agent': 'LYC Client' }

  conn = httplib.HTTPConnection( host )
  conn.request("POST","/api/login", params, headers)
  response = conn.getresponse() 

  print response.read().strip()


返回示例 ::

  $ python t_post.py 
  {"code": 0, "session_key": "0ebfda3c29a9d961c181e2a9424b88e72aa93003", "desc": "Welcome to LYC."}



验证用户
=========

- URL: /api/login
- method: POST
- request args ::

    username: string
    password: string ( 明文，后台 sha1 加密验证 )

- return ::

    {
        code: Number,     # 返回状态
        desc: String,     # 返回信息描述
        session_key: 用户的会话 key
    }


获取虚拟机基本信息
===================

- URL: /api/instance/baseinfo
- method: POST
- request args ::

    session_key: 用户的会话 key
    instance_id: Number

- return ::

    {
        code: Number,
        desc: String,
        vdi_type: Number,  # 默认是 1, 表示 spice
        host: String,
        port: Number,
    }


示例 ( get_instance_info.py ) ::

  #!/usr/bin/env python 
  # _*_ coding: utf-8 _*_ 

  import base64 
  import urllib 
  import httplib 
  import sys
 
  api = "/api/instance/baseinfo"
  instance_id = sys.argv[1]
  session_key = 'be26574d62df76b1b131984cc8b9c85cf6ea1496'
  host = '127.0.0.1'

  params = urllib.urlencode({'instance_id': instance_id,
                             'session_key': session_key})
  auth = base64.b64encode('cleartext username'+ ':'+ 'cleartext passwords') 
  headers = {"Authorization": "Basic "+ auth,
             'Content-Type': 'application/x-www-form-urlencoded',
             'User-Agent': 'LYC Client' }

  conn = httplib.HTTPConnection( host )
  conn.request("POST", api, params, headers)
  response = conn.getresponse() 

  print response.read().strip()


用法 ::

  $ python get_instance_info.py 2252
  {"instance_id": 2252, "host": "10.0.0.2", "code": 0, \
   "vdi_type": 1, "port": null, \
   "desc": "Information about openerp7 img gz"}

  $ python get_instance_info.py 5
  {"code": 1, "desc": "Instance %s is someone else's"}



获取用户虚拟机列表
===================

- URL: /api/myun/instance
- method: POST
- request args ::

    sepa: Number  # 一次列出多少项， 默认 10
    p: Number     # 当前页 

- return ::

    {
        code: 数字,
        desc: 补充描述返回信息,
        list: [ { id: 虚拟机 ID,
                  name: 虚拟机名字,
                  summary: String,
                  status: Number,
                  status_string: String,
                 },
                 ...
              ]
    }


示例 ( get_my_instances.py ) ::

  #!/usr/bin/env python 
  # _*_ coding: utf-8 _*_ 

  import base64 
  import urllib 
  import httplib 
  import sys
 
  api = "/api/myun/instance"
  session_key = 'be26574d62df76b1b131984cc8b9c85cf6ea1496'
  host = '127.0.0.1'

  params = urllib.urlencode({'session_key': session_key,
                             'sepa': 2, 'p': 1})
  auth = base64.b64encode('cleartext username'+ ':'+ 'cleartext passwords') 
  headers = {"Authorization": "Basic "+ auth,
             'Content-Type': 'application/x-www-form-urlencoded',
             'User-Agent': 'LYC Client' }

  conn = httplib.HTTPConnection( host )
  conn.request("POST", api, params, headers)
  response = conn.getresponse()

  print response.read().strip()


用法 ::

  $ python get_my_instances.py 
  {"code": 0, "list": [\
   {"status": 2, "summary": null, "id": 2252, \
    "status_string": "instance is stopped", \
    "name": "openerp7 img gz"}, \
   {"status": 1, "summary": null, "id": 2492, \
    "status_string": "new instance that hasn't run once", \
    "name": "gallery3"}, \
   {"status": 1, "summary": null, "id": 2493, \
    "status_string": "new instance that hasn't run once", \
    "name": "ubuntu 12.04 64\u4f4d\u7248"}\
  ], "desc": "List 3 instances"}
