# Patchless XMLRPC Service for Django
# Kind of hacky, and stolen from Crast on irc.freenode.net:#django
# Self documents as well, so if you call it from outside of an XML-RPC Client
# it tells you about itself and its methods
#
# Brendan W. McAdams <brendan.mcadams@thewintergrp.com>

# SimpleXMLRPCDispatcher lets us register xml-rpc calls w/o
# running a full XMLRPC Server.  It's up to us to dispatch data

from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Create a Dispatcher; this handles the calls and translates info to function maps
#dispatcher = SimpleXMLRPCDispatcher() # Python 2.4
dispatcher = SimpleXMLRPCDispatcher(allow_none=False, encoding=None) # Python 2.5

 
@csrf_exempt
def rpc_handler(request):
        """
        the actual handler:
        if you setup your urls.py properly, all calls to the xml-rpc service
        should be routed through here.
        If post data is defined, it assumes it's XML-RPC and tries to process as such
        Empty post assumes you're viewing from a browser and tells you about the service.
        """

        if len(request.POST):
                response = HttpResponse(mimetype="application/xml")
                response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
        else:
                response = HttpResponse()
                response.write("<b>This is an XML-RPC Service.</b><br>")
                response.write("You need to invoke it using an XML-RPC Client!<br>")
                response.write("The following methods are available:<ul>")
                methods = dispatcher.system_listMethods()

                for method in methods:
                        # right now, my version of SimpleXMLRPCDispatcher always
                        # returns "signatures not supported"... :(
                        # but, in an ideal world it will tell users what args are expected
                        sig = dispatcher.system_methodSignature(method)

                        # this just reads your docblock, so fill it in!
                        help =  dispatcher.system_methodHelp(method)

                        response.write("<li><b>%s</b>: [%s] %s" % (method, sig, help))

                response.write("</ul>")
                response.write('<a href="http://www.djangoproject.com/"> <img src="http://media.djangoproject.com/img/badges/djangomade124x25_grey.gif" border="0" alt="Made with Django." title="Made with Django."></a>')

        response['Content-length'] = str(len(response.content))
        return response

def multiply(a, b):
        """
        Multiplication is fun!
        Takes two arguments, which are multiplied together.
        Returns the result of the multiplication!
        """
        return a*b



import json
from lyweb.app.domain.models import Domain
from lyweb.app.node.models import Node


def update_domain_status(id, status):
    '''
    Update the domain status
    '''

    domain = Domain.objects.get(pk=id)
    domain.status = status
    domain.save()
    return 0

def update_node(data):

    try:
        N = json.loads(data)
    except:
        return 1

    ip = N.get('ip', None)
    if not ip:
        return 2

    try:
        node = Node.objects.get(ip = ip)
        node.hostname = N.get('hostname', None)
        port = N.get('port', None)
    except:
        try:
            node = Node(ip = ip, hostname = N.get('hostname', None), port = N.get('port', None))
        except:
            return 3

    try:
        node.status = N.get('status', "unknown")
        node.maxcpus = N.get('maxcpus', 1)
        node.memory = N.get('memory', 0)
        node.cpu_model = N.get('cpu_model', 'unknown')
        node.cpu_mhz = N.get('cpu_mhz', 0)
        node.hypervisor = N.get('hypervisor', 'unknown')
        node.hypervisor_version = N.get('hypervisor_version', 'unknown')
        node.libversion = N.get('libversion', 'unknown')
        node.save()
        return 0
    except:
        return 4


def update_node_status(data):

    try:
        N = json.loads(data)
    except:
        return 1

    ip = N.get('ip', None)
    if not ip:
        return 2

    try:
        node = Node.objects.get(ip = ip)
        node.status = N.get('status', None)
        node.save()
    except:
        return 3

    return 0


def domain_info(id, attr):

    try:
        domain = Domain.objects.get(id = id)
    except:
        return 'can not found the domain'

    if attr == 'name':
        return domain.name
    elif attr == 'url_path':
        if domain.diskimg:
            return domain.diskimg.url_path
        else:
            return 'no disk img'
    elif attr == 'path':
        if domain.diskimg:
            return domain.diskimg.path
        else:
            return 'no disk img'
    elif attr == 'xmlconf':
        return 'http://192.168.0.12/domain/%s/conf/' % id
    else:
        return "unknown attr: %s" % attr



# you have to manually register all functions that are xml-rpc-able with the dispatcher
# the dispatcher then maps the args down.
# The first argument is the actual method, the second is what to call it from the XML-RPC side...
dispatcher.register_function(multiply, 'multiply')
dispatcher.register_function(update_domain_status, 'update_domain_status')
dispatcher.register_function(update_node, 'update_node')
dispatcher.register_function(update_node_status, 'update_node_status')
dispatcher.register_function(domain_info, 'domain_info')


# Ref: https://code.djangoproject.com/wiki/XML-RPC
# Example:
#import sys
#import xmlrpclib
#rpc_srv = xmlrpclib.ServerProxy("http://localhost:8000/xml_rpc_srv/")
#result = rpc_srv.multiply( int(sys.argv[1]), int(sys.argv[2]))
#print "%d * %d = %d" % (sys.argv[1], sys.argv[2], result)
