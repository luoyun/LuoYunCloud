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



## i18n

I18N_PATH = os.path.join(PROJECT_ROOT, "locale")

LANGUAGES = (
    ('zh_CN', u'简体中文'),
#    ('zh_TW', u'繁體中文'),
    ('en_US', 'English'),
)



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


