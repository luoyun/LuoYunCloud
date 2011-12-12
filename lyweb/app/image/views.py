import os
from django.utils.translation import ugettext as _

from django.db import IntegrityError
from django.core.exceptions import ValidationError

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.util import render_to, build_form, checksum_md5

from lyweb.app.image.models import Image, ImageCatalog, ImageOriginInfo, IMAGE_TYPE
from lyweb import LuoYunConf as lyc



@render_to('image/index.html')
def index(request):

    popularity_images = Image.objects.all().order_by('-popularity')
    image_catalogs = ImageCatalog.objects.all()
    images = Image.objects.all()

    return { 'popularity_images': popularity_images,
             'image_catalogs': image_catalogs,
             'images': images }



@render_to('image/catalog.html')
def catalog(request, id):

    try:
        c = ImageCatalog.objects.get(pk=id)
    except ImageCatalog.DoesNotExist:
        return { 'error': _('Catalog %s have not found !')  % id }

    return { 'catalog': c }



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

    YD = { 'IMAGE_TYPE': IMAGE_TYPE,
           'IMAGE_LIST': IMAGE_LIST,
           'filetype': 3,
           'catalogs': catalogs }


    if request.method != 'POST':
        return YD


    # Now it's POST
    name = request.POST.get('name', None)
    filetype = request.POST.get('filetype', None)
    filename = request.POST.get('filename', None)
    catalog_id = request.POST.get('catalog', None)

    YD['name'] = name
    YD['filetype'] = int(filetype)
    YD['filename'] = filename
    YD['catalog'] = int(catalog_id)
    #print YD

    err = 0
    if not name:
        YD['name_error'] = _('This field is required !')
        err += 1

    if not filename:
        YD['filename_error'] = _('This field is required !')
        err += 1

    if err:
        return YD

    try:
        catalog = ImageCatalog.objects.get(pk=YD['catalog'])
    except ImageCatalog.DoesNotExist:
        YD['catalog_error'] = _('Catalog %s have not found !')  % YD['catalog_id']
        return YD

    # 1. compute md5 of the file
    real_path = os.path.join(lyc.LY_IMAGE_UPLOAD_PATH, YD['filename'])
    checksum_value = checksum_md5(real_path)
    if not checksum_value:
        YD['submit_error'] = _('get md5 checksum on file %s have error.') % real_path
        return YD

    # Check exist of image
    r, s = image_exists(checksum_value)
    if r:
        # TODO: correct the image
        YD['submit_error'] = _('Image exist: %s !') % s
        return YD


    # 4. create the OriginInfo
    # Fix Me: added by user
    try:
        origin = ImageOriginInfo(
            name = filename,
            author = "LuoYun.CO",
            summary = "Support by LuoYun.CO",
            description = "http://www.luoyun.co",
            creat_time = '2011-10-1',
            version = 1,
            checksum_type = 1,
            checksum_value = checksum_value )
        origin.save()
    except ValidationError, emsg:
        YD['submit_error'] = _('ValidationError, cannot create origin: %s') % emsg
        return YD

    # 5. create image
    try:
        image = Image( user = request.user,
                       name = YD['name'],
                       filetype = YD['filetype'],
                       checksum_type = 1,
                       checksum_value = checksum_value,
                       filename = checksum_value + ".image",
                       catalog = catalog,
                       origin = origin )
        image.save()
    except IntegrityError, emsg:
        YD['submit_error'] = _('IntegrityError: %s' % emsg)
        return YD
    except ValueError, emsg:
        YD['submit_error'] = _('ValueError: %s' % emsg)
        return YD
    except ValidationError, emsg:
        YD['submit_error'] = _('ValidationError: %s') % emsg
        return YD

    # Register image to storage
    r, s = register_image(image)
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

    url = reverse('image:catalog', args=[c.id])
    return HttpResponseRedirect(url)





@render_to('image/image_view.html')
def view_image(request, id):

    image = Image.objects.get(pk = id)

    return { 'image': image }


@render_to('image/ajax_image_show.html')
def ajax_image_show(request, id):

    image = Image.objects.get(pk = id)

    return { 'image': image }




# Check the status of image
def image_exists(md5):

    origin = None
    image = None

    # Does checksum exist in ImageOriginInfo ?
    try:
        origin = ImageOriginInfo.objects.get(checksum_value=md5)
    except ImageOriginInfo.DoesNotExist:
        pass

    # Does checksum exist in Image ?
    try:
        image = Image.objects.get(checksum_value=md5)
    except Image.DoesNotExist:
        pass


    if origin or image:
        err = _('checksum %s exist in') % md5
        if origin:
            err += " ImageOriginInfo (id = %s)" % origin.id
        if image:
            err += " Image (id = %s)" % image.id
        return (True, err)
    else:
        return (False, _("checksum %s does not exist") % md5)


def register_image(image):

    # root path of image
    rpath = os.path.join(lyc.LY_IMAGE_PATH, str(image.id))
    if not os.path.exists(rpath):
        try:
            os.mkdir(rpath)
        except OSError, emsg:
            return (False, _("create %s error: %s") % (rpath, emsg))

    # src image file path
    spath = os.path.join(lyc.LY_IMAGE_UPLOAD_PATH, image.origin.name)
    if not os.path.exists(spath):
        return (False, _("could not foud %s") % spath)

    # image file path
    ipath = os.path.join(rpath, image.filename)
    if not os.path.exists(ipath):
        try:
            os.link(spath, ipath)
            os.unlink(spath)
        except OSError, emsg:
            return (False, _("save %s error: %s") % (rpath, emsg))

    return (True, _("register image to storage success ."))
