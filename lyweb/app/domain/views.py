from django.utils.translation import ugettext as _

from django.db import IntegrityError
from django.core.exceptions import ValidationError

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.app.domain.models import AppCatalog, Domain
from lyweb.app.image.models import Image

from lyweb.util import render_to, build_form, lyw_struct_pack

from lyweb.LuoYunConf import LY_CLC_DAEMON as DS # Daemon Server
from lyweb.LuoYunConf import LYWEB_DOMAIN_LIFECYCLE_FLAG, LYWEB_DOMAIN_CONTROL_FLAG
from lyweb.LuoYunConf import LYCMD_TYPE

import lyweb.LuoYunConf as lyc
from lyweb.LuoYunConf import LYWEB_JOB_TARGET_TYPE
from lyweb.LuoYunConf import LYWEB_JOB_ACTION
from lyweb.LuoYunConf import LYWEB_JOB_STATUS
from lyweb.app.job.util import new_job

from lyweb.LuoYunConf import LST_WEB_S, LST_CONTROL_S, RQTYPE_NEW_JOB

import struct



@render_to('domain/index.html')
def index(request):

    YD = { 'title': _('Instances Home'),
           'catalogs': [],
           'total': 0 }

    if request.user.is_authenticated():
        catalogs = AppCatalog.objects.filter(user=request.user)
        for c in catalogs:
            Ds = Domain.objects.filter(catalog = c.id)
            YD['catalogs'].append((c, len(Ds)))
        YD['domains'] = Domain.objects.filter(user=request.user, catalog = None)
    else:
        YD['domains'] = Domain.objects.all()

    YD['total'] = len(YD['domains'])

    return YD


@render_to('domain/domain_list.html')
def domain_list(request):

    domains = Domain.objects.all()

    return { 'domains': domains }



@render_to('domain/conf.xml')
def get_domain_conf(request, id):

    domain = Domain.objects.get(pk=id)

    return { 'domain': domain }

# The config of domain
@render_to('domain/config.txt')
def get_domain_config(request, id):

    domain = Domain.objects.get(pk=id)

    return { 'domain': domain, 'HOST_URL': lyc.HOST_URL }

# The config of osmanager
@render_to('domain/LuoYun.conf')
def osmanager_config(request, id):

    domain = Domain.objects.get(pk=id)

    return { 'domain': domain,
             'CONTROL_SERVER_IP': lyc.LY_CLC_DAEMON_HOST,
             'CONTROL_SERVER_PORT': lyc.LY_CLC_DAEMON_PORT }


@login_required
def domain_control(request, id, control):

    '''
    Control action of the domain.
    '''

    try:
        domain = Domain.objects.get(pk=id)
    except:
        return HttpResponse(u'ERROR: have not found domain %s' % id)

    name = domain.name
    if ( len(name) > 32 ):
        return HttpResponse(u'name is to long: "%s"' % name)

    # New Job
    target_type = LYWEB_JOB_TARGET_TYPE.get('domain', 0)
    action = LYWEB_JOB_ACTION.get(control, 0)
    job = new_job(request.user, target_type, id, action)
    sockhead = struct.pack('iiii', LST_WEB_S, RQTYPE_NEW_JOB, 4, job.id)
    ##sockhead = struct.pack('iiii', LST_WEB_S, RQTYPE_NEW_JOB, 4, 1)
    try:
        DS.sendall(sockhead)
    except:
        job.status = LYWEB_JOB_STATUS.get('failed', 0)
        job.save()
        return HttpResponse(u'Send msg to control server daemon error! May be it have not running ?')

    return HttpResponseRedirect( reverse('domain:index') )



@render_to('domain/view_domain.html')
def view_domain(request, id):

    try:
        domain = Domain.objects.get(pk = id)
    except Domain.DoesNotExist:
        return { 'DoesNotExist': True, 'ID': id }


    return { 'domain': domain }



@login_required
@render_to('domain/add_domain.html')
def add_domain(request, image_id = 0):

    YD = { 'title': _('Create New Domain'),
           'image': int(image_id), 'name_error': None,
           'image_error': None, 'catalog_error': None,
           'submit_error': None }
    YD['catalogs'] = AppCatalog.objects.filter(user=request.user)
    YD['images'] = Image.objects.all()

    if request.method != 'POST':
        return YD

    # Now it's POST
    YD['name'] = request.POST.get('name', None)
    YD['summary'] = request.POST.get('summary', "")
    YD['description'] = request.POST.get('description', "")
    YD['image'] = int(request.POST.get('image', 0))
    YD['catalog'] = int(request.POST.get('catalog', 0))

    if not YD['name']:
        YD['name_error'] = _('This field is required !')

    if not YD['image']:
        YD['image_error'] = _('This field is required !')
    else:
        try:
            image = Image.objects.get(pk = YD['image'])
        except Image.DoesNotExist:
            YD['image_error'] = _('Image %s does not exist !' % YD['image'])

    catalog = None
    if YD['catalog']:
        try:
            catalog = AppCatalog.objects.get(pk = YD['catalog'])
        except AppCatalog.DoesNotExist:
            YD['catalog_error'] = _('Catalog %s does not exist !' % YD['catalog'])

    if YD['name_error'] or YD['image_error'] or YD['catalog_error']:
        return YD

    try:
        d = Domain( name = YD['name'], user = request.user,
                    summary = YD['summary'],
                    description = YD['description'],
                    image = image )
        if catalog:
            d.catalog = catalog
        d.save()
        # TODO: id >= 65536
        d.mac = '92:1B:40:26:%02x:%02x' % (
            d.id / 256, d.id % 256)
        d.save()

    except IntegrityError, emsg:
        YD['submit_error'] = _('IntegrityError: %s' % emsg)
    except ValueError, emsg:
        YD['submit_error'] = _('ValueError: %s' % emsg)
    except ValidationError, emsg:
        YD['submit_error'] = _('ValidationError: %s') % emsg
    except:
        YD['submit_error'] = _('Create Instance error')

    if YD['submit_error']:
        return YD
    
    url = reverse('domain:view', args=[d.id])
    return HttpResponseRedirect(url)



@login_required
@render_to('domain/edit_domain.html')
def edit_domain(request, id = 0):

    YD = { 'title': _('Edit Instance'), 'domain': None,
           'name_error': None, 'image_error': None,
           'catalog_error': None, 'submit_error': None }

    try:
        domain = Domain.objects.get(pk = id)
        YD['domain'] = domain
    except Domain.DoesNotExist:
        YD['submit_error'] = _('The domain %s does not exist !' % id)
        return YD

    YD['catalogs'] = AppCatalog.objects.filter(user=request.user)
    YD['images'] = Image.objects.all()


    if request.method != 'POST':
        return YD

    # Now it's POST
    YD['name'] = request.POST.get('name', None)
    YD['summary'] = request.POST.get('summary', "")
    YD['description'] = request.POST.get('description', "")
    YD['image'] = int(request.POST.get('image', 0))
    YD['catalog'] = int(request.POST.get('catalog', 0))

    if not YD['name']:
        YD['name_error'] = _('This field is required !')

    if not YD['image']:
        YD['image_error'] = _('This field is required !')
    else:
        try:
            image = Image.objects.get(pk = YD['image'])
        except Image.DoesNotExist:
            YD['image_error'] = _('Image %s does not exist !' % YD['image'])

    catalog = None
    if YD['catalog']:
        try:
            catalog = AppCatalog.objects.get(pk = YD['catalog'])
        except AppCatalog.DoesNotExist:
            YD['catalog_error'] = _('Catalog %s does not exist !' % YD['catalog'])

    if YD['name_error'] or YD['image_error'] or YD['catalog_error']:
        return YD

    try:
        domain.name = YD['name']
        domain.summary = YD['summary']
        domain.description = YD['description']
        domain.image = image
        if catalog:
            domain.catalog = catalog
        domain.save()
    except IntegrityError, emsg:
        YD['submit_error'] = _('IntegrityError: %s' % emsg)
    except ValueError, emsg:
        YD['submit_error'] = _('ValueError: %s' % emsg)
    except ValidationError, emsg:
        YD['submit_error'] = _('ValidationError: %s') % emsg
    except:
        YD['submit_error'] = _('Create Instance error')

    if YD['submit_error']:
        return YD
    
    url = reverse('domain:view', args=[domain.id])
    return HttpResponseRedirect(url)



@login_required
@render_to('domain/delete_domain.html')
def delete_domain(request, id):

    YD = { 'title': _('Delete the Instance !'),
           'delete_error': None }

    try:
        domain = Domain.objects.get(pk = id)
    except Domain.DoesNotExist:
        YD['delete_error'] = _('The domain %s does not exist !' % id)

    if request.user != domain.user:
        YD['delete_error'] = _('Just %s can delete this domain !' % domain.user)

    if domain.status == 2:
        YD['delete_error'] = _('The domain is running now, please shutdown it first !')

    if YD['delete_error']:
        return YD

    try:
        domain.delete()
    except:
        YD['delete_error'] = _('System error')

    return YD



@render_to('domain/view_catalog.html')
def view_catalog(request, id):

    try:
        c = AppCatalog.objects.get(pk=id)
    except AppCatalog.DoesNotExist:
        return { 'error': _('Catalog %s have not found !')  % id }

    return { 'catalog': c }


@render_to('domain/view_catalog_ajax.html')
def view_catalog_ajax(request, id):

    c = None

    if id == '0':
        domains = Domain.objects.all()
    else:
        domains = Domain.objects.filter(catalog=id)
        try:
            c = AppCatalog.objects.get(pk=id)
        except AppCatalog.DoesNotExist:
            return { 'error': _('Catalog %s have not found !')  % id }

    return { 'catalog': c, 'domains': domains }



@login_required
@render_to('domain/add_catalog.html')
def add_catalog(request):

    if request.method != 'POST':
        return {}


    name = request.POST.get('name', None)
    summary = request.POST.get('summary', "")
    description = request.POST.get('description', "")
    if not name:
        return { 'name_error': _('This field is required !'),
                 'name': name,
                 'summary': summary,
                 'description': description }
    try:
        c = AppCatalog( name = name, user = request.user,
                        summary = summary,
                        description = description )
        c.save()
    except:
        return { 'submit_error': _('Add catalog error'),
                 'name': name,
                 'summary': summary,
                 'description': description }

    url = reverse('domain:view_catalog', args=[c.id])
    return HttpResponseRedirect(url)
