from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.util import render_to, build_form

from lyweb.app.image.models import Image
from lyweb.app.image.forms import ImageRegisterForm



@render_to('image/index.html')
def index(request):

    images = Image.objects.all()

    return { 'images': images }


@login_required
@render_to('image/register.html')
def register(request):

    form = build_form(ImageRegisterForm, request, user = request.user)

    if form.is_valid():
        image = form.save()
        if not image:
            return HttpResponse(u'ERROR: file exists!')
        else:
            return HttpResponseRedirect( reverse ('image:index') )

    return { 'form': form }


@render_to('image/image_view.html')
def view_image(request, id):

    image = Image.objects.get(pk = id)

    return { 'image': image }


@render_to('image/ajax_image_show.html')
def ajax_image_show(request, id):

    image = Image.objects.get(pk = id)

    return { 'image': image }


