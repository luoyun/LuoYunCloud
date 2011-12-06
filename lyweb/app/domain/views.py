from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.app.domain.models import Domain
from lyweb.util import render_to, build_form, lyw_struct_pack

from lyweb.app.domain.forms import DomainSimpleCreateForm
from lyweb.LuoYunConf import LY_CLC_DAEMON as DS # Daemon Server
from lyweb.LuoYunConf import LYWEB_DOMAIN_LIFECYCLE_FLAG, LYWEB_DOMAIN_CONTROL_FLAG
from lyweb.LuoYunConf import LYCMD_TYPE

from lyweb.LuoYunConf import LYWEB_JOB_TARGET_TYPE
from lyweb.LuoYunConf import LYWEB_JOB_ACTION
from lyweb.LuoYunConf import LYWEB_JOB_STATUS
from lyweb.app.job.util import new_job

from lyweb.LuoYunConf import LST_WEB_S, LST_CONTROL_S, LA_WEB_NEW_JOB

import struct



@render_to('domain/index.html')
def index(request):

    domains = Domain.objects.all()

    return { 'domains': domains }


@render_to('domain/domain_list.html')
def domain_list(request):

    domains = Domain.objects.all()

    return { 'domains': domains }

@render_to('domain/show_domain.html')
def show_domain(request, id):

    try:
        domain = Domain.objects.get(pk=id)
    except:
        return HttpResponse(u'ERROR: have not found domain %s' % id)

    return {'domain': domain}


@login_required
@render_to('domain/simple_create.html')
def simple_create(request):

    form = build_form(DomainSimpleCreateForm, request, user = request.user)

    if form.is_valid():
        domain = form.save()
        return HttpResponseRedirect( reverse ('domain:index') )

    return { 'form': form }


@render_to('domain/conf.xml')
def get_domain_conf(request, id):

    domain = Domain.objects.get(pk=id)

    return { 'domain': domain }


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
    sockhead = struct.pack('iiiiii', LST_WEB_S, LST_CONTROL_S,
                           0, LA_WEB_NEW_JOB, 4, job.id)
    try:
        DS.sendall(sockhead)
    except:
        job.status = LYWEB_JOB_STATUS.get('failed', 0)
        job.save()
        return HttpResponse(u'Send msg to control server daemon error! May be it have not running ?')

    return HttpResponseRedirect( reverse('domain:index') )



# Some Utils
from lyweb.app.node.models import Node

def find_node_for_new_domain():

    nodes = Node.objects.all()

    if nodes:
        node = nodes[0]
    else:
        node = None

    return node
