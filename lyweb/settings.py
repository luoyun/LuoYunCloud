# coding: utf-8

import os, sys, ConfigParser

## Global PATH
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'lib'))
#print sys.path

LUOYUN_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'luoyun.cfg')

STATIC_PATH = os.path.join(PROJECT_ROOT, "static")
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "template")
STATIC_URL = "/static/"

#THEME = "default"
THEME = "default2"
THEME_URL = "/static/themes/%s/" % THEME

#ATTACHMENT
ATTACHMENT_PATH = os.path.join(PROJECT_ROOT, "static/attachment")
ATTACHMENT_URL = "/static/attachment/"
ATTACHMENT_MAXSIZE = 10 * 1024 * 1024 # 10M

# Nignx config path
DEFAULT_NGINX_CONF_PATH = '/etc/nginx/conf.d/'
DEFAULT_NGINX_LOG_PATH = '/opt/LuoYun/logs/nginx/'
DEFAULT_NGINX_BIN_PATH = '/usr/sbin/nginx'

SITE_CONFIG = LUOYUN_CONFIG_PATH
cf = ConfigParser.ConfigParser()
cf.read( LUOYUN_CONFIG_PATH )

if cf.has_option('base', 'appliance_top_dir'):
    appliance_top_dir = cf.get('base', 'appliance_top_dir')
else:
    appliance_top_dir = '/opt/LuoYun/data/appliance/'

if cf.has_option('base', 'appliance_top_url'):
    appliance_top_url = cf.get('base', 'appliance_top_url')
else:
    appliance_top_url = '/dl/appliance/'

if cf.has_option('clc', 'clc_ip'):
    control_server_ip = cf.get('clc', 'clc_ip')
else:
    control_server_ip = '127.0.0.1'
if cf.has_option('clc', 'clc_port'):
    control_server_port = int(cf.get('clc', 'clc_port'))
else:
    control_server_port = 1369

if cf.has_option('base', 'admin_email'):
    ADMIN_EMAIL = cf.get('base', 'admin_email')
else:
    ADMIN_EMAIL = 'contact@luoyun.co'


# Layout
if cf.has_option('base', 'layout'):
    DEFAULT_LAYOUT = cf.get('base', 'layout')
else:
    DEFAULT_LAYOUT = 'VPS' # home page is appliance


# User resource limit
USER_DEFAULT_MEMORY = 256    # 256 M
USER_DEFAULT_CPUS = 1        # 1 core
USER_DEFAULT_INSTANCES = 10  # 10 instance
USER_DEFAULT_STORAGE = 2     # 2 G

USER_ACTIVE_MIN = 30*60 # Min actie time for user, seconds.


# INSTANCE display
INSTANCE_HOME_PAGE_SIZE=50
APPLIANCE_INSTANCE_LIST_PAGE_SIZE=10
MYUN_INSTANCE_LIST_PAGE_SIZE=10

INSTANCE_SLIST_ALL=[1, 2, 3, 4, 5]
INSTANCE_SLIST_RUNING=[3, 4, 5]
INSTANCE_SLIST_STOPED=[1, 2]

# ADMIN display
ADMIN_USER_LIST_PAGE_SIZE=50


# Email Setting
MAIL_SENDER = 'LuoYunCloud Administrator'  # Sender name
MAIL_HOST = None  # SMTP server
MAIL_PORT = 25    # SMTP port
MAIL_FROM = None  # From email address
MAIL_USER = None  # login username
MAIL_PASS = None  # login password

from settings import cf

if cf.has_option('email', 'smtp_server'):
    MAIL_SERVER = cf.get('email', 'smtp_server')

if cf.has_option('email', 'smtp_port'):
    MAIL_PORT = int( cf.get('email', 'smtp_port') )

if cf.has_option('email', 'name'):
    MAIL_SENDER = cf.get('email', 'name')

if cf.has_option('email', 'from'):
    MAIL_FROM = cf.get('email', 'from')

if cf.has_option('email', 'username'):
    MAIL_USER = cf.get('email', 'username')

if cf.has_option('email', 'password'):
    MAIL_PASS = cf.get('email', 'password')

if MAIL_USER and '@' in MAIL_USER:
    if not MAIL_FROM:
        MAIL_FROM = MAIL_USER


## i18n

I18N_PATH = os.path.join(PROJECT_ROOT, "locale")

LANGUAGES = (
    ('zh_CN', u'简体中文'),
#    ('zh_TW', u'繁體中文'),
    ('en_US', 'English'),
)


MAX_STORAGE_SIZE=60 # 60G

# Socket Request

PKT_TYPE_WEB_NEW_JOB_REQUEST = 10001
JOB_S_INITIATED = 100
JOB_S_FAILED = 311

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
    'REBOOT_INSTANCE': 205, # LY_A_NODE_REBOOT_INSTANCE = 205,
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
INSTANCE_DELETED_STATUS = 100



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
    'app.message',
    'app.myun',
    ]


luoyun_system_config = [
    # ( 'key', 'value' )
    #('network.pool.start', '192.168.1.100'),
    #('network.pool.end', '192.168.1.254'),
    #('network.netmask', '255.255.255.0'),
    #('network.gateway', '192.168.1.1'),
    #('network.nameserver', '8.8.8.8'),
]

default_permission = [
    # ( 'codename', 'name' )
    ('admin', 'Administrator'),
    #('user', 'User'),  # default permission for all user
    ('appliance.upload', 'Can upload appliance'),
    ('instance.create', 'Can create instance'),
    ('network.add', 'Can add another NIC configure'),
]

default_group = [
    # ( 'group name' )
    ('admin'),
    ('user'),
]

default_user = [
    # ( 'username', 'password' )
    ('admin', 'admin'),
]

default_admin_user = 'admin'

default_user_group = [
    # ( 'group name', 'username' )
    ('admin', 'admin'),
]

default_user_permission = [
    # ( 'username', 'permission codename' )
    #('admin', 'admin'),
    #('luoyun', 'user'),
]

default_group_permission = [
    # ( 'group name', 'permission codename' )
    ('admin', 'admin'),
    #('user', 'user'),
    ('user', 'appliance.upload'),
    ('user', 'instance.create'),
]


default_appliance_catalog = [
    # ( 'name', 'summary' )
    ('LuoYun', 'Default Catalog'),
#    ('Office', 'Office support'),
#    ('OS Platform', 'Base os platform'),
]


default_wiki_catalog = [
    # ( 'name', 'summary' )
    ('Default', 'Default Catalog'),
]



# TODO: restart main program

CMD_ARGV=''
def restart_luoyun_web():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    global CMD_ARGV
    print 'restart_luoyun_web: CMD_ARGV = ', CMD_ARGV
    python = sys.executable
    os.execl(python, python, *CMD_ARGV)


USER_AVATAR_MAXSIZE = 2 * 1024 * 1024 # 2M
USER_AVATAR_NAME = 'uavatar.png'
USER_AVATAR_MINI_NAME = 'uavatar-mini.png'
USER_AVATAR_THUM_SIZE = (120, 120)
USER_AVATAR_MINI_THUM_SIZE = (36, 36)
USER_AVATAR_DEFAULT = os.path.join(STATIC_URL, 'image/user2.png')
USER_AVATAR_MINI_DEFAULT = 'image/user-mini.png'

APPLIANCE_LOGO_MAXSIZE = 2 * 1024 * 1024 # 2M
APPLIANCE_LOGO_DEFAULT = os.path.join(STATIC_PATH, 'image/appliance.png')
APPLIANCE_LOGO_DEFAULT_URL = os.path.join(STATIC_URL, 'image/appliance.png')

APPLIANCE_LOGO_NAME = 'alogo.png'
APPLIANCE_LOGO_THUM_NAME = 'thum_alogo.png'

APPLIANCE_LOGO_THUM_SIZE = (120, 120)


INSTANCE_LOGO_DEFAULT_URL = os.path.join(STATIC_URL, 'image/instance.png')
INSTANCE_LOGO_NAME = 'ilogo.png'
INSTANCE_LOGO_MARK = os.path.join(STATIC_PATH, 'image/instance-watermark.png' )

# Instance status check interval time
INSTANCE_S_UP_INTER_1 = 3  # seconds
INSTANCE_S_UP_INTER_2 = 6  # seconds
