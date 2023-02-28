from django.views.generic import TemplateView
from django.shortcuts import render
from celery.contrib.abortable import AbortableTask, AbortableAsyncResult
from django.http import HttpResponse, HttpResponseRedirect
from celery import shared_task
from celery_progress.websockets.backend import WebSocketProgressRecorder
from celery.utils.log import get_task_logger
import time
import datetime
from django import forms
import requests
from bs4 import BeautifulSoup
import json

from .models import DashboardSettings
from profiles.models import Profile

HARD_CODED_COUNT_LIMIT = 3 # TODO UPDATE!

class DashboardSettingsForm(forms.Form):
    profile_name = forms.CharField(label='Your bandcamp username', max_length=100, required=True)
    delay_time = forms.FloatField(label='Page Crawl Delay (in s)', required=True, initial=1.0, min_value=0.001)
    depth = forms.IntegerField(label='Profile Crawl Depth', required=True, initial=0, min_value=0, 
                               help_text="This specifies how many recursive crawls into the users you follow \
                               our crawler will go. I.e., how deep the 'you're following x who follows xx who \
                                follows xxx...' rabbit hole goes ")

def init_dashboard_settings(request, cur_delay=None, cur_profile=None, depth=None, error_msg=""):
    print("init_dashboard")
    form = DashboardSettingsForm()
    if cur_delay is not None:
        form.delay_time = cur_delay
    if cur_profile is not None:
        form.profile_name = Profile.get(id=cur_profile).username
    if depth is not None:
        form.depth = depth
    return render(request, 'dashboard_settings_form.html', {'form': form, 'error_msg': error_msg})

def post_dashboard_settings(request):
    error_msgs = []
    if request.method == 'POST':
        form = DashboardSettingsForm(request.POST)
        if form.is_valid():            
            try:
                url = 'https://bandcamp.com/' + form.cleaned_data['profile_name']
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')

                data = soup.find_all("div", attrs={"data-blob":True})[0]
                data_blob = json.loads(data['data-blob'])

                profile_obj, _ = Profile.objects.get_or_create(id=int(data_blob['fan_data']['fan_id']))
                profile_obj.username = form.cleaned_data['profile_name']
                profile_obj.name = data_blob['fan_data']['name']
                profile_obj.img_id = int(data_blob['fan_data']['photo']['image_id'])
                profile_obj.save()
                
                try:
                    settings_obj, _ = DashboardSettings.objects.get_or_create(lock='X')
                    settings_obj.delay_time = form.cleaned_data['delay_time']
                    settings_obj.base_profile = profile_obj
                    settings_obj.max_profile_depth = form.cleaned_data['depth']
                    settings_obj.save()

                    return HttpResponseRedirect('/dashboard')

                except Exception as e:
                    error_msgs.append("ERROR: could not update settings")
                    print(e)
                    
            except Exception as e:
                error_msgs.append("ERROR: Invalid bandcamp username") 
                print(form.profile_name, e)       
        else:
            error_msgs.append("ERROR: invalid form")
    
    error_msg = " | ".join(error_msgs)
    if DashboardSettings.objects.count() == 0:
        return init_dashboard_settings(request, error_msg=error_msg)
    settings_obj = DashboardSettings.objects.get(lock='X')
    if settings_obj.delay_time is None or settings_obj.base_profile is None or settings_obj.max_profile_depth is None:
        return init_dashboard_settings(request, settings_obj.delay_time, settings_obj.base_profile, settings_obj.max_profile_depth, error_msg=error_msg)

def pre_dashboard_wrapper(request):
    # Handle initialization of dashboard settings here:
    if DashboardSettings.objects.count() == 0:
        return init_dashboard_settings(request)
    settings_obj = DashboardSettings.objects.get(lock='X')
    if settings_obj.delay_time is None or settings_obj.base_profile is None or settings_obj.max_profile_depth is None:
        return init_dashboard_settings(request, settings_obj.delay_time, settings_obj.base_profile, settings_obj.max_profile_depth)

    return HttpResponseRedirect('/dashboard')

def dashboard_wrapper(request, ajax_content_link=None):
    if DashboardSettings.objects.count() == 0:
        return HttpResponseRedirect('/')
    settings_obj = DashboardSettings.objects.get(lock='X')
    if settings_obj.delay_time is None or settings_obj.base_profile is None or settings_obj.max_profile_depth is None:
        return HttpResponseRedirect('/')

    if ajax_content_link is None:
        if Profile.objects.count() == 1:
            ajax_content_link = '/dashboard/prompt_update'
        else:
            ajax_content_link = '/dashboard/landing'    

    base_profile_img_url = "https://f4.bcbits.com/img/" + str(settings_obj.base_profile.img_id).zfill(10) + "_41.jpg"        

    return render(request, '_post_dashboard_base.html', 
                  {'ajax_content_link': ajax_content_link, 
                   'base_profile_obj': settings_obj.base_profile,
                   'base_profile_img_url': base_profile_img_url})
        
def prompt_update(request):
    return HttpResponse("PROMPT HERE")

    # if Profile.objects.count() == 1:
    #     return prompt_update(request)

    # TODO
    # add edit settings link

    # TODO
    # update
        # completed date
        # return values
        # select update checkboxes

    # TODO
    # profile explorer
    # D3.js

    # TODO
    # release explorer

    # TODO
    # label explorer

    # TODO
    # bins


    return HttpResponse("reached the end of the dashboard. weird?")









logger = get_task_logger(__name__)

def log_completed():
    print("(^*)^*^)*^)*^)*^)*^ LOGGING COMPLETED")

def log_aborted():
    print("(^*)^*^)*^)*^)*^)*^ LOGGING ABORTED")

@shared_task(bind=True, base=AbortableTask)
def my_task(self,seconds):
    progress_recorder = WebSocketProgressRecorder(self)
    result = 0
    for i in range(seconds):
        time.sleep(1)
        if self.is_aborted():
            log_aborted()
            return -1
        result += i
        logger.info(f'current status: {i}')
        progress_recorder.set_progress(i + 1, seconds, description="myprogressdesc")
    log_completed()
    return result

def progress_view(request):
    check = AbortableAsyncResult('django-test-main')    
    return render(request, 'display_progress.html', context={'task_state': check.state})    

def progress_view_abort(request):
    check = AbortableAsyncResult('django-test-main')
    check.abort()
    print("!!!!!!!!!!!!!!!!!aborting", check.state)
    return HttpResponse("")

def progress_view_run(request):
    check = AbortableAsyncResult('django-test-main')
    if check.state != "PROGRESS":
        check.forget()
        check = my_task.apply_async((30,), task_id='django-test-main')
    return HttpResponse("")
    
def progress_view_reset(request):
    check = AbortableAsyncResult('django-test-main')
    check.forget()
    print("RESET: ", datetime.datetime.now())
    return HttpResponse("")