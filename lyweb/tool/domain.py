import json
import os
import logging
import subprocess
import settings

from app.site.models import SiteConfig
from app.instance.models import Instance


def _get_nginx_conf(db):

    nginx_conf = settings.NGINX_CONF

    nginx_site_conf = db.query(SiteConfig).filter_by(
        key = 'nginx' ).first()

    if nginx_site_conf and nginx_site_conf.value:
        nginx_conf.update( json.loads( nginx_site_conf.value ) )


    conf_path  = nginx_conf.get('conf_path', '')
    log_path   = nginx_conf.get('log_path' , '')
    template   = nginx_conf.get('template' , '')
    nginx_path = nginx_conf.get('nginx' , '')

    # make sure nginx is exists and executable
    if not ( os.path.isfile( nginx_path ) and
             os.access( nginx_path, os.X_OK) ):
        return False, _('"%s" is not exist or executable.') % nginx_path

    # make sure dir exists
    for p in ( conf_path, log_path ):
        if os.path.exists( p ): continue

        try:
            os.makedirs(p)
        except Exception, e:
            return False, _('Create dir "%s" failed: %s') % (p, e)

    if not template:
        return False, _('Template is empty.')


    return True, nginx_conf



def instance_domain_binding(db, I):

    ret, nginx_conf = _get_nginx_conf(db)
    if not ret:
        return ret, nginx_conf

    domains = [ I.default_domain ]

    for d in I.domains:
        domains.append( d.domain )

    if not domains:
        return False, _("Can not get domains.")

    # TODO: binding only one ip now.
    ip = I.access_ip

    # TODO: can not binding when no ip found !
    if not ip:
        return False, _("Can not get access ip.")


    nginx_log  = os.path.join( nginx_conf['log_path'],
                               'i.%s.log'  % I.id )
    default_domain = domains[0]
    domain_list = ' '.join(domains)

    vh = ''
    for virtual_port, real_port in [ (80, 80),
                                     (8080, 8080),
                                     (8001, 8001) ]:
        try:
            vh += nginx_conf['template'] % {
                'default_domain': default_domain,
                'domain_list': domain_list,
                'ip': ip,
                'virtual_port': virtual_port,
                'real_port': real_port,
                'access_log': nginx_log,
                }

        except Exception, msg:
            return False, _('Output virtual host failed: %s') % msg

    # update nginx file
    cf = os.path.join( nginx_conf['conf_path'], 'i.%s.conf' % I.id)
    cmd = '%s -s reload' % nginx_conf['nginx']

    try:
        f = open(cf, 'w')
        f.write( vh )
        f.close()

        subprocess.check_call( cmd.split() )

    except Exception, e:
        try:
            os.unlink( cf ) # delete nginx conf file
        except:
            pass

        return False, _('Update nginx failed: %s') % e


    # He laughs best who laughs last. ;-)

    logging.info('instance %(id)s: binding %(domains)s success.' % {
            'id': I.id, 'domains': domain_list })

    return True, _("OK")



def instance_domain_unbinding(db, I):

    ret, nginx_conf = _get_nginx_conf(db)
    if not ret:
        return ret, nginx_conf

    # update nginx file
    cf = os.path.join( nginx_conf['conf_path'], 'i.%s.conf' % I.id)
    cmd = '%s -s reload' % nginx_conf['nginx']

    try:
        os.unlink( cf ) # delete nginx conf file
        subprocess.check_call( cmd.split() )

    except Exception, e:
        return False, e

    logging.info('instance %s: unbinding domains success.' % I.id)

    # He laughs best who laughs last. ;-)
    return True, _("OK")



