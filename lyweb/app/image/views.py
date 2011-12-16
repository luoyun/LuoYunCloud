import os, hashlib
from django.utils.translation import ugettext as _

from django.db import IntegrityError
from django.core.exceptions import ValidationError

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.util import render_to, build_form, checksum_md5

from lyweb.app.domain.models import Domain
from lyweb.app.image.models import Image, ImageCatalog, ImageOriginInfo, IMAGE_TYPE

from lyweb import LuoYunConf as lyc



@render_to('image/index.html')
def index(request):

    YD = { 'title': _('Appliances Home'),
           'catalogs': [],
           'total': 0 }

    catalogs = ImageCatalog.objects.all()
    images = Image.objects.all()

    for c in catalogs:
        Is = Image.objects.filter(catalog = c.id)
        YD['catalogs'].append((c, len(Is)))

    YD['total'] = len(images)
    YD['images'] = images


    return YD



@render_to('image/view_catalog.html')
def view_catalog(request, id):

    try:
        c = ImageCatalog.objects.get(pk=id)
    except ImageCatalog.DoesNotExist:
        return { 'error': _('Catalog %s have not found !')  % id }

    return { 'catalog': c }


@render_to('image/view_catalog_ajax.html')
def view_catalog_ajax(request, id):

    c = None

    if id == '0':
        images = Image.objects.all().order_by('-popularity')
    else:
        images = Image.objects.filter(catalog=id)
        try:
            c = ImageCatalog.objects.get(pk=id)
        except ImageCatalog.DoesNotExist:
            pass

    return { 'catalog': c, 'images': images }



@render_to('image/origin.html')
def origin(request, id):

    try:
        o = ImageOriginInfo.objects.get(pk=id)
    except ImageOriginInfo.DoesNotExist:
        return { 'error': _('OriginInfo %s have not found !')  % id }

    return { 'origin': o }



@login_required
@render_to('image/add_image.html')
def add_image(request):

    # Filelist on
    IMAGE_LIST = []
    for f in os.listdir(lyc.LY_IMAGE_UPLOAD_PATH):
        fullpath = os.path.join(lyc.LY_IMAGE_UPLOAD_PATH, f)
        if os.path.isfile(fullpath):
            IMAGE_LIST.append(f)

    catalogs = ImageCatalog.objects.all()
    origins = ImageOriginInfo.objects.all()

    YD = { 'IMAGE_TYPE': IMAGE_TYPE,
           'IMAGE_LIST': IMAGE_LIST,
           #'filetype': 3,
           'catalogs': catalogs,
           'origins': origins,
           'submit_error': None,
           'name_error': None,
           'addmethod_error': None,
           'filename_error': None,
           'catalog_error': None,
           'origin_error': None }


    if request.method != 'POST':
        return YD

    # Now it's POST
    name = request.POST.get('name', None)
    #filetype = request.POST.get('filetype', 0)
    addmethod = int(request.POST.get('addmethod', 0))
    filename = request.POST.get('filename', None)
    catalog_id = request.POST.get('catalog', 0)
    origin_id = request.POST.get('origin', 0)

    YD['name'] = name
    #YD['filetype'] = int(filetype)
    YD['filename'] = filename
    YD['catalog'] = int(catalog_id)
    YD['origin'] = int(origin_id)
    YD['addmethod'] = int(addmethod)

    # Check value of POST
    if not catalog_id:
        YD['catalog_error'] = _('Catalog must be select !')
    else:
        try:
            catalog = ImageCatalog.objects.get(pk=YD['catalog'])
        except ImageCatalog.DoesNotExist:
            YD['catalog_error'] = _('Catalog %s have not found !')  % YD['catalog']

    if not origin_id:
        YD['origin_error'] = _('Origin must be select !')
    else:
        try:
            origin = ImageOriginInfo.objects.get(pk=YD['origin'])
        except ImageOriginInfo.DoesNotExist:
            YD['origin_error'] = _('OriginInfo %s have not found !')  % YD['origin']

    if not name:
        YD['name_error'] = _('This field is required !')

    if addmethod not in [1, 2]:
        YD['addmethod_error'] = _('Unknown addmethod')

    if (addmethod != 1) and (not YD['filename']):
        YD['filename_error'] = _('This field is required !')

    if ( YD['catalog_error'] or 
         YD['origin_error'] or
         YD['name_error'] or
         YD['addmethod_error'] or
         YD['filename_error'] ):
        return YD

    checksum_value = None
    if addmethod == 1:
        # Upload image from user agent
        try:
            UF = request.FILES['file']
            YD['filename'] = UF.name
            checksum = hashlib.md5()
            real_path = '/opt/LuoYun/upload/%s' % UF.name
            #print "name = %s\nsize = %s" % (UF.name, UF.size)
            destination = open(real_path, 'wb+')
            for chunk in UF.chunks():
                destination.write(chunk)
                checksum.update(chunk)
            destination.close()
            checksum_value = checksum.hexdigest()
        except:
            YD['addmethod_error'] = _('Upload %s to %s error' % (UF.name, real_path))
    elif addmethod == 2:
        real_path = os.path.join(lyc.LY_IMAGE_UPLOAD_PATH, YD['filename'])
        # compute md5 of the file
        checksum_value = checksum_md5(real_path)
    else:
        YD['addmethod_error'] = _('Unknown addmethod') # Should not go here, but who sure ?

    if not checksum_value:
        YD['submit_error'] = _('get md5 checksum on file %s have error.') % real_path
        return YD

    # Check exist of image
    r, s = image_exists(checksum_value)
    if r:
        # TODO: correct the image
        YD['submit_error'] = _('Image exist: %s !') % s
        return YD

    # create image
    try:
        image = Image( user = request.user,
                       name = YD['name'],
                       #filetype = YD['filetype'],
                       filetype = 3, # TODO: check from file
                       checksum_type = 1,
                       checksum_value = checksum_value,
                       filename = YD['filename'],
                       catalog = catalog,
                       origin = origin )
        image.size = os.path.getsize(real_path)
        image.save()
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

    # Register image to storage
    r, s = register_image(image, real_path)
    if not r:
        YD['submit_error'] = _('Register image to storage error: %s') % s
        return YD

    # change the status to OK
    image.status = 1
    image.save()

    url = reverse('image:view', args=[image.id])
    return HttpResponseRedirect(url)



@login_required
@render_to('image/add_catalog.html')
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
        c = ImageCatalog( name = name,
                          summary = summary,
                          description = description )
        c.save()
    except:
        return { 'submit_error': _('Add catalog error'),
                 'name': name,
                 'summary': summary,
                 'description': description }

    url = reverse('image:view_catalog', args=[c.id])
    return HttpResponseRedirect(url)



@login_required
@render_to('image/add_origin.html')
def add_origin(request):

    YD = { 'title': _('Add new origin') }

    if request.method != 'POST':
        return YD

    YD['name'] = request.POST.get('name', None)
    YD['home'] = request.POST.get('name', "")
    YD['summary'] = request.POST.get('summary', "")
    YD['description'] = request.POST.get('description', "")

    if not YD['name']:
        YD['name_error'] = _('This field is required !')
        return YD

    try:
        o = ImageOriginInfo( name = YD['name'],
                             summary = YD['summary'],
                             description = YD['description'] )
        o.save()
    except:
        YD['submit_error'] = _('Add origininfo error')
        return YD

    url = reverse('image:origin', args=[o.id])
    return HttpResponseRedirect(url)



@render_to('image/view_image.html')
def view_image(request, id):

    try:
        image = Image.objects.get(pk = id)
    except Image.DoesNotExist:
        return { 'DoesNotExist': True, 'ID': id }


    return { 'image': image }



@login_required
@render_to('image/edit_image.html')
def edit_image(request, id):

    YD = { 'IMAGE_TYPE': IMAGE_TYPE, 'ID': id,
           'name_error': None, 'catalog_error': None }

    try:
        image = Image.objects.get(pk = id)
        YD['image'] = image
    except Image.DoesNotExist:
        YD['DoesNotExist'] = True
        return YD

    YD['catalogs'] = ImageCatalog.objects.all()
    #YD['origins'] = ImageOriginInfo.objects.all()

    if request.method != 'POST':
        return YD


    # Now it's POST
    name = request.POST.get('name', None)
    catalog_id = int(request.POST.get('catalog', 0))

    if not name:
        YD['name_error'] = _('Unsupported name')

    if not catalog_id:
        YD['catalog_error'] = _('Please select a catalog')
    else:
        try:
            catalog = ImageCatalog.objects.get(pk = catalog_id)
        except ImageCatalog.DoesNotExist:
            YD['catalog_error'] = _('catalog %d does not exist') % catalog_id

    if YD['name_error'] or YD['catalog_error']:
        return YD

    try:
        image.name = name
        image.catalog = catalog
        image.save()
        url = reverse('image:view', args=[image.id])
        return HttpResponseRedirect(url)
    except:
        YD['submit_error'] = _('Can not save image')

    return YD



@permission_required('image.delete_image')
#@login_required
@render_to('image/delete_image.html')
def delete_image(request, id):

    YD = { 'title': _('Delete the image !'), 'ID': id,
           'delete_error': None, 'DoesNotExist': False,
           'domains': None }

    try:
        image = Image.objects.get(pk = id)
    except Image.DoesNotExist:
        YD['DoesNotExist'] = True
        return YD

    try:
        domains = Domain.objects.filter(image = image.id)
    except:
        YD['delete_error'] = _('System error, can not find domains')

    if domains:
        YD['domains'] = domains
        YD['delete_error'] = _('There are domains used this appliance, can not delete now !')

    if YD['delete_error']:
        return YD

    try:
        image.delete()
    except OSError, emsg:
        YD['delete_error'] = _('System error: %s' % emsg)

    return YD





# Check the status of image
def image_exists(md5):

    # Does checksum exist in Image ?
    try:
        image = Image.objects.get(checksum_value=md5)
        return (True, _('checksum %s exist in') % md5)
    except Image.DoesNotExist:
        return (False, _("checksum %s does not exist") % md5)



def register_image(image, srcfile):

    # top path dir of image object
    if not os.path.exists(image.top_path):
        try:
            os.mkdir(image.top_path)
        except OSError, emsg:
            return (False, _("create %s error: %s") % (image.top_path, emsg))

    # full path of image file
    if os.path.exists(image.path):
        return (True, _("%s is exist already, remove manually if you need.") % image.path)
    else:
        try:
            os.link(srcfile, image.path)
            os.unlink(srcfile)
            return (True, _("register image to storage success ."))
        except OSError, emsg:
            return (False, _("save %s to %s error: %s") % (srcfile, image.path, emsg))
        except:
            return (False, _("system error"))



