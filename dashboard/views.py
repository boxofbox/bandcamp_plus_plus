from django.views.generic import TemplateView
from django.shortcuts import render
from celery.contrib.abortable import AbortableTask, AbortableAsyncResult
from django.http import HttpResponse

class DashboardView(TemplateView):
    template_name = "dashboard.html"


from celery import shared_task
from celery_progress.websockets.backend import WebSocketProgressRecorder
from celery.utils.log import get_task_logger
import time
import datetime
from threading import Lock

lock = Lock()

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