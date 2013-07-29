"""
BVD v1.0

Copyright (c) 2012 Voltage Security
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import urllib2, types, os

from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.utils import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.models import User
from django.core import serializers


from bvd.jenkins.jenkins import RetrieveJob
from bvd.pull import models, forms
from bvd.decorators.decorators import secure_required

def append_http(hostname):
    if not hostname: return 'http://'
    
    if hostname.find('http') > -1 or hostname.find('https') > -1:
        return hostname
    else:
        return 'http://%s' % hostname

def widget_to_dictionary(widget):
    if isinstance(widget, models.UserCiJob):
        return dict(
            pk = widget.pk,
            ci_server = widget.ci_server.pk,
            hostname = widget.ci_server.hostname,
            jobname = widget.jobname,
            displayname = widget.displayname,
            width = widget.width,
            height = widget.height,
            status = widget.status,
            readonly = widget.readonly,
            icon = widget.icon,
            user = widget.user.pk,
            entity_active = widget.entity_active,
        )
    else:
        raise TypeError
   
def get_jobs_for_readonly():
    jobs = models.UserCiJob.objects.filter(entity_active=True)
    joblist = []
    for job in jobs:
        d = dict(
            pk      = job.pk,
            hostname = job.ci_server.hostname,
            jobname = job.jobname,
            displayname = job.displayname,
            width = job.width,
            height = job.height,
            status = job.status,
            readonly = True,
            icon = job.icon,
        )
        joblist.append(d)
    return joblist

def get_jobs_for_user(user, *args):
    jobs =  models.UserCiJob.objects.filter(entity_active=True,user__username=user.username)
    list = []
    for job in jobs:
        if len(args) > 0:
            job.readonly = args[0]
            job.save()
        d = dict(
            pk      = job.pk,
            hostname = job.ci_server.hostname,
            jobname = job.jobname,
            displayname = job.displayname,
            width = job.width,
            height = job.height,
            status = job.status,
            readonly = job.readonly,
            icon = job.icon,   
        )
        list.append(d)
        
    return list

def save_ci_server(**widget):
    try:
        ci_server = models.CiServer.objects.get(hostname=append_http(widget['hostname']))
    except models.CiServer.DoesNotExist:
        ci_server = forms.CiServerForm(data=widget).save()
    
    return ci_server

    
def save_user_ci_job(**widget):
    ci_server = save_ci_server(**widget)
    widget['ci_server'] = ci_server.pk

    try:
        user_ci_job = models.UserCiJob.objects.get(user__pk=widget['user'], jobname=widget['jobname'])
        form = forms.UserCiJobForm(data=widget, instance=user_ci_job)
        if form.is_valid():
            user_ci_job = form.save()
    except models.UserCiJob.DoesNotExist:
        form = forms.UserCiJobForm(widget)
        if form.is_valid():
            user_ci_job = form.save()
        else:
            print form.errors
    return user_ci_job 
    
def redirect_to_home(request):
    return HttpResponseRedirect('/')

@secure_required
def home(request,template='index.html'):
    appletv = request.GET.get('appletv')
    if appletv == '1':
        return render_to_response(template,
                                  dict(title="Welcome to BVD", readonly=True, appletv=True),
                                  context_instance=RequestContext(request))

    if settings.USE_SSL:
        import socket
        if socket.gethostbyname(request.META['SERVER_NAME']) == request.META['REMOTE_ADDR']:
            readonly = False
        else:
            readonly = True
    else:
        readonly = False
    return render_to_response(template,
                              dict(title='Welcome to BVD', readonly = readonly),
                              context_instance=RequestContext(request))

@secure_required
def login(request):
    if 'view_tv' in request.POST:
        return HttpResponse(simplejson.dumps([dict(status = 200, readonly = True)]), content_type = 'application/javascript; charset=utf8')
    else:    
        readonly = False
        username = request.POST.get('username')
        password = request.POST.get('password1')
    
        user = authenticate(username=username,password=password)
        if user and user.is_active:
            django_login(request,user)
            return HttpResponse(simplejson.dumps([dict(status = 200, readonly = readonly)]), content_type = 'application/javascript; charset=utf8')
    
    return HttpResponse(simplejson.dumps([dict(status = 500)]), content_type = 'application/javascript; charset=utf8')

@secure_required
def logout(request):
    django_logout(request)
    return HttpResponse(simplejson.dumps([dict(status = 200)]), content_type = 'application/javascript; charset=utf8')
            
@secure_required
def validate_username(request):
    username = request.POST.get('username')
    
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse(simplejson.dumps([dict(status = 200)]), content_type = 'application/javascript; charset=utf8')

    return HttpResponse(simplejson.dumps([dict(status = 500)]), content_type = 'application/javascript; charset=utf8')
 
@secure_required
def validate_hostname(request):
    print request.POST.get('hostname')
    job = RetrieveJob(append_http(request.POST.get('hostname',None)),None)
    print request.POST.get('username') == 'Username'
    test = job.lookup_hostname(request.POST.get('username') != 'Username', request.POST.get('username'), request.POST.get('password1'))
    
    if test == urllib2.URLError:
        result = dict(status = 500)
    elif test == ValueError:
        result = dict(status = 404)
    elif test == 403: #autherization required
        result = dict(status = 403)
    elif test == 401: #invalid cerendtials
        result = dict(status = 401)
    else:
        result = dict(status = 200)
    
    return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')
    
@secure_required
def validate_job(request):
    hostname = append_http(request.POST.get('hostname',''))
    jobname = request.POST.get('jobname',None)

    if hostname.strip() == 'http://' or not jobname:
        result = dict(status = 500)
        return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')
  
    job = RetrieveJob(hostname,jobname)
    result = job.lookup_job(request.POST.get('username') != 'Username', request.POST.get('username'), request.POST.get('password1'))

    if result == urllib2.URLError:
        result = dict(status = 500)
        return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')
    elif result == ValueError:
        result = dict(status = 404)
        return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')
    elif result == 403: #autherization required
        result = dict(status = 403)
    elif result == 401: #invalid cerendtials
        result = dict(status = 401)
        return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')
    elif not result['status']:
            result['status'] = 'SUCCESS'
    else:
        result.update(dict(hostname = hostname))
        
    key = str('%s/%s' % (hostname, jobname))
    
    request.session[key] = result
    return HttpResponse(simplejson.dumps([dict(status = 200)]), content_type = 'application/javascript; charset=utf8')
    
@secure_required
def retrieve_job(request):

    if not request.user.is_authenticated():
        result = [dict(status = 401)]
        return HttpResponse(simplejson.dumps(result), content_type = 'application/javascript; charset=utf8')

    hostname = append_http(request.POST.get('hostname',''))
    jobname = request.POST.get('jobname',None)
    displayname = request.POST.get('displayname')

    if hostname.strip() == 'http://' or not jobname:
        result = [dict(status = 500)]
        return HttpResponse(simplejson.dumps(result), content_type = 'application/javascript; charset=utf8')

    key = str('%s/%s' % (hostname, jobname))
    result = request.session[key]

    if not result:
        result = dict(status = 500)
        return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')

    #check to see if the user has already added the job
    user_ci_job = models.UserCiJob.objects.filter(entity_active=True, jobname=jobname, user__username=request.user.username)
    if len(user_ci_job) > 0:
        result = dict(status = 100)
        return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')

    widget = dict(
         hostname = hostname,
         jobname = jobname,
         displayname = displayname,
         status = result['status'],
         user = request.user.pk,
         icon = 'checkmark.png',
         readonly = False,
         entity_active = True,
    )
    user_ci_job = save_user_ci_job(**widget)
    result.update(dict(displayname = displayname, jobname = jobname, pk = user_ci_job.pk, icon = 'checkmark.png'))
        
    return HttpResponse(simplejson.dumps([result]), content_type = 'application/javascript; charset=utf8')


@secure_required
def save_jobs(request):
    if not request.user.is_authenticated():
        result = [dict(status = 401)]
        return HttpResponse(simplejson.dumps(result), content_type = 'application/javascript; charset=utf8')
    
    user = request.user
    widgets = simplejson.loads(request.POST['widgets'])
    
    if not widgets:
        result = [dict(status = 500)]
        return HttpResponse(simplejson.dumps(result), content_type = 'application/javascript; charset=utf8')
    
    for widget in widgets:
        widget['user'] = user.pk
        widget['entity_active'] = True
        save_user_ci_job(**widget)
    result = [dict(status = 200)]
    return HttpResponse(simplejson.dumps(result), content_type = 'application/javascript; charset=utf8')

@secure_required    
def autocomplete_hostname(request):
    txt = request.POST.get('txt')
    servers = models.CiServer.objects.filter(hostname__icontains=txt)
    result = [server.hostname for server in servers]
    #result = ['http://localhost:80%d' % i for i in range(5)]
    return HttpResponse(simplejson.dumps(result), content_type = 'application/javascript; charset=utf8')
    

@secure_required    
def get_modal(request):
    template = request.GET.get('template') 
    if template == 'add_job':
        if not request.user.is_authenticated():
            template = 'login_required.html'
            return render_to_response(template,
                  dict(),
                  context_instance=RequestContext(request))
    if template == 'edit_widget':
        if not request.user.is_authenticated():
            template = 'login_required.html'
            return render_to_response(template,
                dict(),
                context_instance=RequestContext(request))
        else:
            widget_id = request.GET.get('widget_id')
            try:
                widget = models.UserCiJob.objects.get(pk=widget_id)
                print widget.id
            except models.UserCiJob.DoesNotExist:
                pass
            form = forms.UserCiJobForm(instance=widget)
            return render(request, 'edit_widget.html', dict(form=form, widget_id=widget.id))
       
    template = '%s.html' % template
    

    return render_to_response(template,
                  request.GET,
                  context_instance=RequestContext(request))
    
def signup(request):
    form = forms.SignupForm(request.POST)
    if form.is_valid():
        form.save()
        user = authenticate(username=request.POST.get('username'),password=request.POST.get('password1'))
        django_login(request, user)
        return HttpResponse(simplejson.dumps([dict(status = 200)]), content_type = 'application/javascript; charset=utf8')
    else:
        return HttpResponse(simplejson.dumps([dict(status = 500)]), content_type = 'application/javascript; charset=utf8')
    
@secure_required    
def remove_job(request):
    user_ci_job = models.UserCiJob.objects.get(pk=int(request.POST.get('pk')))
    user_ci_job.entity_active = False
    user_ci_job.save()
    return HttpResponse(simplejson.dumps([dict(status = 200)]), content_type = 'application/javascript; charset=utf8')

@secure_required
def pull_jobs(request, *args, **kwargs):
    
    if request.user.is_authenticated():
        list = get_jobs_for_user(request.user)
        for job in list:
            jenkins = RetrieveJob(job['hostname'],job['jobname'])
            result = jenkins.lookup_job()
            
            if result == urllib2.URLError:
                #TODO: add an additional state other than down 
                job['status'] = "DOWN"
            elif result == ValueError:
                #TODO: add an additional state other than down
                job['status'] = "DOWN"
            elif not result['status']:
                job['status'] = 'SUCCESS'
            elif job['status'] == 'ABORTED' or job['status'] == 'NOT_BUILT':
                job['status'] = "DOWN"
            else:
                job['status'] = result['status'] 

            
        return HttpResponse(simplejson.dumps([dict(status = 200, jobs = list)]), content_type = 'application/javascript; charset=utf8')

def pull_apple_tv_jobs(request, *args, **kwargs):
    joblist = get_jobs_for_readonly()
    for job in joblist:
        jenkins = RetrieveJob(job['hostname'],job['jobname'])
        result = jenkins.lookup_job()

        print result
            
        if result == urllib2.URLError:
           #TODO: add an additional state other than down 
            job['status'] = "DOWN"
        elif result == ValueError:
            #TODO: add an additional state other than down
            job['status'] = "DOWN"
        elif not result['status']:
            job['status'] = 'SUCCESS'
        elif job['status'] == 'ABORTED' or job['status'] == 'NOT_BUILT':
            job['status'] = "DOWN"
        else:
            job['status'] = result['status'] 
            
    return HttpResponse(simplejson.dumps([dict(status = 200, jobs = joblist)]), content_type = 'application/javascript; charset=utf8')

@secure_required
def save_widget(request):
    """
        This Function:
            Is POST-ed to by the edit_widget modal in order to save changes
            to the widget.
    """
    if not request.user.is_authenticated():
        return HttpResponse(status=401)

    if 'widget_id' in request.POST:
        new_data = request.POST.copy()
        widget = models.UserCiJob.objects.get(pk=request.POST['widget_id'])
        old_data = widget_to_dictionary(widget)

        # The form has to be populated by old data because the edit_widget
        # modal form doesn't provide all attributes of the UserCiJob model.
        # The widget's attributes are copied to a dictionary and then
        # the values from the form data are used to update the dictionary.

        for key in ['displayname', 'jobname', 'entity_active', 'ci_server']:
            if key in new_data:
                old_data[key] = new_data[key]

        # If the form provides a new CiServer hostname a new model object is
        # created and then the ci_server value is changed in the form data to match.

        if 'new_ci_server' in new_data and not new_data['new_ci_server'] == '':
            job = RetrieveJob(append_http(new_data['new_ci_server']),None)
            if job.lookup_hostname(False):
                newserver = models.CiServer(hostname = new_data['new_ci_server'])
                newserver.save()
                old_data['ci_server'] = newserver.hostname

        form = forms.UserCiJobForm(old_data, instance=widget)
        if form.is_valid():
            form.save()
        else:
            print form.errors

    return HttpResponseRedirect('/')

def edit_widget_image(request):
    if request.method == 'POST':
        try:
            user_ci_job = models.UserCiJob.objects.get(id=request.POST.get('widget_id'))
            user_ci_job.icon = request.FILES.get('icon').name
            user_ci_job.save()

            if settings.DEBUG:
                path = '%s/pull/static/images/' % (settings.PROJECT_ROOT,)
            else:
                path = '%s/images/' % (settings.STATIC_ROOT,)

            file = open('%s%s' % (path, request.FILES.get('icon').name,), 'wb')
            file.write(request.FILES.get('icon').read())
            file.close()
        except Exception, e:
            print e.message
            pass
    return pull_jobs(request)