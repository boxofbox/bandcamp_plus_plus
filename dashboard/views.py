from django.views.generic import TemplateView
from django.shortcuts import render
from celery.result import AsyncResult
from celery.contrib.abortable import AbortableTask, AbortableAsyncResult

class DashboardView(TemplateView):
    template_name = "dashboard.html"


from celery import shared_task
from celery_progress.backend import ProgressRecorder
from celery.utils.log import get_task_logger
import time
from threading import Lock

lock = Lock()

logger = get_task_logger(__name__)

@shared_task(bind=True, base=AbortableTask)
def my_task(self,seconds):
    lock.acquire()
    try:
        self.update_state(state="PENDING", meta={"testflag":"testing"})
        time.sleep(5)
    finally:
        lock.release()

    progress_recorder = ProgressRecorder(self)
    result = 0
    for i in range(seconds):
        time.sleep(1)
        if self.is_aborted():
            logger.warn(f'aborting signal received')
            return
        result += i
        logger.info(f'current status: {i}')
        progress_recorder.set_progress(i + 1, seconds, description="myprogressdesc")
    return result

def progress_view(request):
    check = AbortableAsyncResult('django-test-main')
    result = my_task.apply_async((30,), task_id='django-test-main')
    print(result.info)
    print("EEHEHEHHEHEHEH")
    return render(request, 'display_progress.html', context={'task_id': result.task_id, 'task_status': result.status, 'task_state': result.state, 'another': "BLANK"})

    """
    if check.state == "SUCCESS":
        
        check.forget()
        result = my_task.apply_async((30,), task_id='django-test-main')
        return render(request, 'display_progress.html', context={'task_id': result.task_id, 'task_status': "WE FOUND SUCCESS!", 'task_state': check.state, 'another': "BLANK"})
    elif check.state == "PROGRESS":
        check.abort()     
        print("######################### confirm abort") 
        print("HERE???????????????????????", check.is_aborted())
        return render(request, 'display_progress.html', context={'task_id': check.task_id, 'task_status': "WE FOUND STARTED!", 'task_state': check.state, 'another': "BLANK"})
    elif check.state == "REVOKED":
        check.forget()
        result = my_task.apply_async((30,), task_id='django-test-main')
        another_result = AsyncResult(result.task_id)
        return render(request, 'display_progress.html', context={'task_id': result.task_id, 'task_status': result.status, 'task_state': result.state, 'another': another_result.status})
    elif check.state == "PENDING":
        result = my_task.apply_async((30,), task_id='django-test-main')
        another_result = AsyncResult(result.task_id)
        return render(request, 'display_progress.html', context={'task_id': result.task_id, 'task_status': result.status, 'task_state': result.state, 'another': another_result.status})
    else:
        return render(request, 'display_progress.html', context={'task_id': "blank", 'task_status': "blank", 'task_state': "blank", 'another': "blank"})
    """

    # TODO: determine if run once
    # TODO: locks for atomic checking
    # TODO: abortable task