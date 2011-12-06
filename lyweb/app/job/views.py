from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from lyweb.app.job.models import Job
from lyweb.util import render_to, build_form, lyw_struct_pack


@render_to('job/index.html')
def index(request):

    jobs = Job.objects.all()
    if jobs:
        jobs = jobs[:10]

    return { 'jobs': jobs }

@render_to('job/job_list.html')
def job_list(request):

    jobs = Job.objects.all()
    if jobs:
        jobs = jobs[:10]

    return { 'jobs': jobs }


