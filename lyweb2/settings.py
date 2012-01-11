# coding: utf-8

import os, sys


## Global PATH
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'lib'))
#print sys.path

STATIC_PATH = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = "/static/"

THEME = "default"
THEME_URL = "/static/themes/%s/" % THEME



## i18n

I18N_PATH = os.path.join(PROJECT_ROOT, "locale")

LANGUAGES = (
    ('zh_CN', u'简体中文'),
#    ('zh_TW', u'繁體中文'),
    ('en_US', 'English'),
)

