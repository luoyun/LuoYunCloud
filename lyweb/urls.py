# coding: utf-8

import os
import tornado.web

from lycustom import LyNotFoundHandler, LyProxyHandler

import app.home.views as home

from app.account.urls import handlers as account_urls
from app.admin.urls import handlers as admin_urls
from app.appliance.urls import handlers as appliance_urls
from app.instance.urls import handlers as instance_urls
from app.wiki.urls import handlers as wiki_urls
from app.job.urls import handlers as job_urls


curdir = os.path.dirname(__file__)

import settings
from settings import JOB_ACTION


settings = {
    'cookie_secret': 'MTMyNTMwNDc3OC40MjA3NjgKCg==',
    'session_secret': 'gAJ9cQAoVQZsb2NhbGVxAVUFemhfQ05xAl',
    'login_url': '/login',
    'no_permission_url': '/no_permission',
    'no_resource_url': '/no_resource',
    'static_path': os.path.join(curdir, 'static'),
    'template_path': os.path.join(curdir, 'template'),
    'gzip': True,
    'debug': True,

    # Global settings about LuoYun System
    'appliance_top_dir': settings.appliance_top_dir,
    'appliance_top_url': settings.appliance_top_url,
    'control_server_ip': settings.control_server_ip,
    'control_server_port': settings.control_server_port,

    'THEME_URL': settings.THEME_URL,
    'STATIC_URL': settings.STATIC_URL,
    'LANGUAGES': settings.LANGUAGES,

    'LYJOB_ACTION': settings.LYJOB_ACTION,
}


handlers =  account_urls + admin_urls + appliance_urls + wiki_urls + instance_urls + job_urls + [

    # Home
    (r'/', home.Index),
    (r'/i18n/setlang', home.SetLocale),
    (r'/no_permission', home.NoPermission),
    (r'/no_resource', home.NoResource),

    # Utils
    (r'/proxy', LyProxyHandler),

    (r'/(.*)', LyNotFoundHandler),
]
