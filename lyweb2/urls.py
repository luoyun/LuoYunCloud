# coding: utf-8

import os
import tornado.web

from lycustom import LyNotFoundHandler, LyProxyHandler

import app.home.views as home
import app.account.views as account
import app.appliance.views as appliance
import app.instance.views as instance
import app.node.views as node
import app.job.views as job
import app.wiki.views as wiki
import app.admin.views as admin


curdir = os.path.dirname(__file__)

import settings
from settings import JOB_ACTION


LYJOB_ACTION = {
    'unknown': 0,
    'run': JOB_ACTION['RUN_INSTANCE'],
    'stop': JOB_ACTION['STOP_INSTANCE'],
    'suspend': 3,
    'save': 4,
    'reboot': 5,
    'query': JOB_ACTION['QUERY_INSTANCE'],
}


settings = {
    'cookie_secret': 'MTMyNTMwNDc3OC40MjA3NjgKCg==',
    'session_secret': 'gAJ9cQAoVQZsb2NhbGVxAVUFemhfQ05xAl',
    'login_url': '/account/login',
    'static_path': os.path.join(curdir, 'static'),
    'template_path': os.path.join(curdir, 'template'),
    'gzip': True,
    'debug': True,

    # Global settings about LuoYun System
    'appliance_top_dir': '/opt/LuoYun/data/appliance/',
    'appliance_top_url': '/dl/appliance/',
    'control_server_ip': '192.168.1.11',
    'control_server_port': 1369,

    'THEME_URL': settings.THEME_URL,
    'STATIC_URL': settings.STATIC_URL,
    'LANGUAGES': settings.LANGUAGES,

    'LYJOB_ACTION': LYJOB_ACTION,
}


handlers = [

    # Home
    (r'/', home.Index),
    (r'/i18n/setlang', home.SetLocale),

    # Account
    (r'/account/login', account.Login),
    (r'/account/logout', account.Logout),
    (r'/account/register', account.Register),
    (r'/account/profile', account.Profile),
    (r'/account/chat', account.Chat),
    (r'/account/online_total', account.Online),
    (r'/account/user_list', account.UserList),
    (r'/account/([0-9]+)', account.User),
    (r'/account/([0-9]+)/reset_password', account.ResetPassword),

    # Application
    (r'/appliance', appliance.Index),
    (r'/appliance/upload', appliance.Upload),
    (r'/appliance/([0-9]+)', appliance.View),
    (r'/appliance/([0-9]+)/edit', appliance.Edit),
    (r'/appliance/([0-9]+)/delete', appliance.Delete),
    (r'/appliance/([0-9]+)/create_instance', appliance.CreateInstance),

    #(r'/appliance/add_catalog', appliance.AddCatalog),


    # Instance
    (r'/instance/add', instance.Add),
    (r'/instance/([0-9]+)', instance.View),
    (r'/instance/([0-9]+)/edit', instance.Edit),
    (r'/instance/([0-9]+)/delete', instance.Delete),
    (r'/instance/([0-9]+)/config', instance.InstanceConfig),
    (r'/instance/([0-9]+)/libvirtd_conf', instance.LibvirtdConf),
    (r'/instance/([0-9]+)/osmanager_conf', instance.OsmanagerConf),

    (r'/instance/([0-9]+)/([a-z]+)', instance.Control),


    # Node
    (r'/node', node.Index),
    (r'/node/dynamic_list', node.DynamicList),
    (r'/node/([0-9]+)', node.Action),

    # Job
    (r'/job', job.Index),
    (r'/job/([0-9]+)/status', job.JobStatus),


    # Wiki
    (r'/wiki', wiki.Index),
    (r'/wiki/topic/([0-9]+)', wiki.ViewTopic),
    (r'/wiki/topic/([0-9]+)/source', wiki.ViewTopicSource),
    (r'/wiki/topic/([0-9]+)/edit', wiki.EditTopic),
    (r'/wiki/topic/([0-9]+)/delete', wiki.DeleteTopic),
    (r'/wiki/topic/add', wiki.NewTopic),
    (r'/wiki/catalog/([0-9]+)', wiki.ViewCatalog),


    # Admin
    (r'/admin', admin.Index),
    (r'/admin/appliance', admin.Appliance),
    (r'/admin/appliance/add_catalog', admin.ApplianceAddCatalog),
    (r'/admin/appliance/catalog/([0-9]+)/edit', admin.ApplianceEditCatalog),
    (r'/admin/wiki', admin.Wiki),
    (r'/admin/wiki/add_catalog', admin.WikiAddCatalog),
    (r'/admin/wiki/catalog/([0-9]+)/edit', admin.WikiEditCatalog),

    # Utils
    (r'/proxy', LyProxyHandler),

    (r'/(.*)', LyNotFoundHandler),
]
