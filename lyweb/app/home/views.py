from django.utils.translation import ugettext as _

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.util import render_to, build_form

from lyweb.app.image.models import Image
from lyweb.app.node.models import Node
from lyweb.app.domain.models import Domain


@render_to("home/index.html")
def index(request):

    images = Image.objects.all()
    nodes = Node.objects.all()
    domains = Domain.objects.all()

    nodes_running = len(Node.objects.filter(status = 2))
    domains_running = len(Domain.objects.filter(status = 2))

    return {'title': _('Welcome To LuoYun'),
            'images': images,
            'images_total': len(images),
            'nodes': nodes,
            'nodes_total': len(nodes),
            'nodes_running': nodes_running,
            'domains': domains,
            'domains_total': len(domains),
            'domains_running': domains_running}


@render_to('home/ajax_domain_list.html')
def ajax_domain_list(request):

    domains = Domain.objects.all()

    return { 'domains': domains }



@render_to('home/login.html')
def login (request):

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            from django.contrib.auth import authenticate, login
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if request.session.test_cookie_worked():
                        request.session.delete_test_cookie()
                        return HttpResponseRedirect(request.session.get('login_redirect_url','/') or '/')
                else:
                    return HttpResponseForbidden(u'inactive account!')

    else:
        request.session['login_redirect_url'] = request.GET.get('next')
        form = AuthenticationForm(request)

    request.session.set_test_cookie()
    return { 'title':_('Login'), 'form':form }



@login_required
def logout(request):
    from django.contrib.auth import logout
    previous_url = request.GET.get('next')
    logout(request)
    return HttpResponseRedirect(previous_url or '/')
