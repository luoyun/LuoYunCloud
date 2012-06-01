# coding: utf-8

import os, sys

## Global PATH
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'lib'))
#print sys.path

STATIC_PATH = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = "/static/"

#THEME = "default"
THEME = "default2"
THEME_URL = "/static/themes/%s/" % THEME

appliance_top_dir = '/opt/LuoYun/data/appliance/'
appliance_top_url = '/dl/appliance/'

#control_server_ip = '127.0.0.1'
control_server_ip = '192.168.1.11'
control_server_port = 1369

ADMIN_EMAIL = 'contact@luoyun.co'



## i18n

I18N_PATH = os.path.join(PROJECT_ROOT, "locale")

LANGUAGES = (
    ('zh_CN', u'简体中文'),
#    ('zh_TW', u'繁體中文'),
    ('en_US', 'English'),
)


# DB Connect format: "postgresql+psycopg2://username:password@HOST_ADDRESS/DB_NAME"
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://luoyun:luoyun@127.0.0.1/luoyun"


# Socket Request

PKT_TYPE_WEB_NEW_JOB_REQUEST = 10001
JOB_S_INITIATED = 100

JOB_TARGET = {
    'NODE': 3,             # JOB_TARGET_NODE
    'INSTANCE': 4,         # JOB_TARGET_INSTANCE
}

JOB_ACTION = {

    # node action
    'ENABLE_NODE': 102,     # LY_A_CLC_ENABLE_NODE = 102
    'DISABLE_NODE': 103,    # LY_A_CLC_DISABLE_NODE = 103

    # instance action
    'RUN_INSTANCE': 201,    # LY_A_NODE_RUN_INSTANCE = 201,
    'STOP_INSTANCE': 202,   # LY_A_NODE_STOP_INSTANCE = 202,
    'DESTROY_INSTANCE': 206,# LY_A_NODE_DESTROY_INSTANCE = 206,
    'QUERY_INSTANCE': 207,  # LY_A_NODE_QUERY_INSTANCE = 207
}


LYJOB_ACTION = {
    'unknown': 0,
    'run': JOB_ACTION['RUN_INSTANCE'],
    'stop': JOB_ACTION['STOP_INSTANCE'],
    'suspend': 3,
    'save': 4,
    'reboot': 5,
    'query': JOB_ACTION['QUERY_INSTANCE'],
}



# TODO
app = [
    'app.home',
    'app.account',
    'app.admin',
    'app.instance',
    'app.node',
    'app.appliance',
    'app.job',
    'app.wiki',
    'app.session',
    'app.system',
    ]


luoyun_system_config = [
    # ( 'key', 'value' )
    ('network.pool.start', '192.168.1.100'),
    ('network.pool.end', '192.168.1.254'),
    ('network.netmask', '255.255.255.0'),
    ('network.gateway', '192.168.1.1'),
    ('network.nameserver', '8.8.8.8'),
]

default_permission = [
    # ( 'codename', 'name' )
    ('admin', 'Administrator'),
    ('user', 'User'),  # default permission for all user
    ('appliance.upload', 'Can upload appliance'),
    ('instance.create', 'Can create instance'),
]

default_group = [
    # ( 'group name' )
    ('admin'),
    ('user'),
]

default_user = [
    # ( 'username', 'password' )
    ('admin', 'admin'),
    ('luoyun', 'luoyun'),  # For test
]

default_admin_user = 'admin'

default_user_group = [
    # ( 'group name', 'username' )
    ('admin', 'admin'),
]

default_user_permission = [
    # ( 'username', 'permission codename' )
    ('admin', 'admin'),
    ('luoyun', 'user'),
]

default_group_permission = [
    # ( 'group name', 'permission codename' )
    ('admin', 'admin'),
    ('user', 'user'),
    ('user', 'appliance.upload'),
    ('user', 'instance.create'),
]


default_appliance_catalog = [
    # ( 'name', 'summary' )
    ('Default', 'Default Catalog'),
    ('Office', 'Office support'),
    ('OS Platform', 'Base os platform'),
]


default_wiki_catalog = [
    # ( 'name', 'summary' )
    ('Default', 'Default Catalog'),
]
