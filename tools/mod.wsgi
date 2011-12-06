import os, sys
sys.path.append('/opt/LuoYunSrc/')
sys.path.append('/opt/LuoYunSrc/lyweb/lib/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'lyweb.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()