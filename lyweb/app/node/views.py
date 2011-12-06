from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.util import render_to, build_form, lyw_struct_pack

from lyweb.app.node.models import Node
from lyweb.app.node.forms import NodeRegisterForm

from lyweb.LuoYunConf import LY_CLC_DAEMON as DS # Daemon Server
from lyweb.LuoYunConf import LYCMD_TYPE, LYWEB_NODE_CONTROL_FLAG

import struct



@render_to('node/index.html')
def index(request):

    nodes = Node.objects.all().order_by('-ip')

    return { 'nodes': nodes }


@render_to('node/node_list.html')
def node_list(request):

    nodes = Node.objects.all().order_by('-ip')

    return { 'nodes': nodes }


@login_required
@render_to('node/register.html')
def register(request):

    form = build_form(NodeRegisterForm, request)

    if form.is_valid():
        node = form.save()
        url = reverse('node:index')
        return HttpResponseRedirect(url)

    return { 'form': form }


@render_to('node/node_view.html')
def view_node(request, id):

    node = Node.objects.get(pk = id)

    return { 'node': node }


@login_required
def node_control(request, id, control):

    '''
    Control action of the node.
    '''

    try:
        node = Node.objects.get(pk=id)
    except:
        return HttpResponse(u'ERROR: node not found.')

    flag = LYWEB_NODE_CONTROL_FLAG.get(control, 0)
    content = struct.pack('ii32s', flag, node.port, str(node.ip))

    length = 40
    cmdtype = LYCMD_TYPE.get('LYCMD_NODE_CONTROL', 0)
    cmd = lyw_struct_pack(cmdtype, length)

    DS.sendall(cmd + content)

    return HttpResponseRedirect( reverse('node:index') )
