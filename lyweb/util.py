from django.shortcuts import render_to_response
from django.template import RequestContext

import struct


def render_to(template):

    def renderer(function):
        def wrapper(request, *args, **kwargs):
            output = function(request, *args, **kwargs)
            if not isinstance(output, dict):
                return output
            tmpl = output.pop('TEMPLATE', template)
            return render_to_response(tmpl, output, context_instance=RequestContext(request))
        return wrapper
    return renderer


def build_form(Form, _request, GET=False, *args, **kwargs):
    """ 
    Shorcut for building the form instance of given form class
    """

    if not GET and 'POST' == _request.method:
        form = Form(_request.POST, _request.FILES, *args, **kwargs)
    elif GET and 'GET' == _request.method:
        form = Form(_request.GET, _request.FILES, *args, **kwargs)
    else:
        form = Form(*args, **kwargs)
    return form


def lyw_struct_pack(cmdtype, length):

    cmd = struct.pack('ii', cmdtype, length)

    return cmd
