import json, os, logging, subprocess
import settings

from app.system.models import LuoYunConfig
from app.instance.models import Instance


def get_instance_domain(db, id):

    domain = db.query(LuoYunConfig).filter_by(key='domain').first()

    if not domain:
        return ''

    domain =  json.loads(domain.value)

    topdomain = domain['topdomain'].strip('.')
    prefix = domain['prefix']
    suffix = domain['suffix']

    subdomain = '%s%s%s' % (prefix, id, suffix)

    return '.'.join([subdomain, topdomain])


def binding_domain_in_nginx(db, id, domain=None):

    domain = domain if domain else get_instance_domain(db, id)

    if not domain:
        return False, _("Can not get domain.")

    nginx = db.query(LuoYunConfig).filter_by(key='nginx').first()
    instance = db.query(Instance).get(id)

    ip = instance.access_ip
    # TODO: can not binding when no ip found !
    if not ip:
        return False, _("Can not get access_ip.")

    NC = json.loads(nginx.value) if nginx else {
        'conf_dir': settings.DEFAULT_NGINX_CONF_PATH,
        'log_dir' : settings.DEFAULT_NGINX_LOG_PATH,
        'bin_path': settings.DEFAULT_NGINX_BIN_PATH }

    for x in (NC['conf_dir'], NC['log_dir'], NC['bin_path']):
        if not os.path.exists( x ):
            return False, _('No such dir or file: %s') % x

    access_log = os.path.join(NC['log_dir'], '%s.log' % domain)
    p = os.path.join(NC['conf_dir'], '%s.conf' % id)

    x = '''
    upstream %(domain)s-%(real_port)s {
        server %(ip)s:%(real_port)s;
    }
    server {
        listen %(access_port)s;
        server_name %(domain)s;

        access_log  %(access_log)s;

        location / {
            proxy_read_timeout 1800;
            client_max_body_size 10m;
            proxy_pass_header Server;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_pass http://%(domain)s-%(real_port)s;
        }
    }
''' % {
            'domain': domain,
            'ip': ip,
            'real_port': 8080,
            'access_port': 8080,
            'access_log': access_log,
}
    y = '''
    upstream %(domain)s-%(real_port)s {
        server %(ip)s:%(real_port)s;
    }
    server {
        listen %(access_port)s;
        server_name %(domain)s;

        access_log  %(access_log)s;

        location / {
            proxy_read_timeout 1800;
            client_max_body_size 512m;
            proxy_pass_header Server;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_pass http://%(domain)s-%(real_port)s;
        }
    }
''' % {
            'domain': domain,
            'ip': ip,
            'real_port': 80,
            'access_port': 80,
            'access_log': access_log,
}
    z = '''
    upstream %(domain)s-%(real_port)s {
        server %(ip)s:%(real_port)s;
    }
    server {
        listen %(access_port)s;
        server_name %(domain)s;

        access_log  %(access_log)s;

        location / {
            proxy_read_timeout 1800;
            client_max_body_size 10m;
            proxy_pass_header Server;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_pass http://%(domain)s-%(real_port)s;
        }
    }
''' % {
            'domain': domain,
            'ip': ip,
            'real_port': 8001,
            'access_port': 8001,
            'access_log': access_log,
}

    f = open(p, 'w')

    f.write(x)
    f.write(y)
    f.write(z)

    f.close()

    # TODO: reload nginx
    cmd = '%s -s reload' % NC['bin_path']

    try:
        subprocess.check_call( cmd.split() )
    #except CalledProcessError, e:
    except Exception, e:
        return False, _('reload nginx error: %s') % e


    # He laughs best who laughs last. ;-)
    return True, _("OK")




def unbinding_domain_from_nginx(db, id):

    nginx = db.query(LuoYunConfig).filter_by(key='nginx').first()

    NC = json.loads(nginx.value) if nginx else {
        'conf_dir': settings.DEFAULT_NGINX_CONF_PATH,
        'log_dir' : settings.DEFAULT_NGINX_LOG_PATH,
        'bin_path': settings.DEFAULT_NGINX_BIN_PATH }

    for x in (NC['conf_dir'], NC['log_dir'], NC['bin_path']):
        if not os.path.exists( x ):
            return False, _('No such dir or file: %s') % x

    # remove config file
    try:
        cf = '%s/%s.conf' % (NC['conf_dir'], id)
        os.unlink( cf )
    except Exception, e:
        # TODO: return failed when config is exist but cann't delete
        if os.path.exists( cf ):
            return False, _('remove nginx config error: %s') % e

    # TODO: reload nginx
    cmd = '%s -s reload' % NC['bin_path']

    try:
        subprocess.check_call( cmd.split() )
    #except CalledProcessError, e:
    except Exception, e:
        return False, _('reload nginx error: %s') % e

    # He laughs best who laughs last. ;-)
    return True, _("OK")

