import time
from celery import shared_task
from celery.contrib.abortable import AbortableTask
from celery_progress.websockets.backend import WebSocketProgressRecorder
from celery.utils.log import get_task_logger
import datetime

from .models import DashboardSettings

logger = get_task_logger(__name__)

def log_completed():
    settings_obj, _ = DashboardSettings.objects.get_or_create(lock='X')        
    settings_obj.main_update_last_completed = datetime.datetime.utcnow()
    settings_obj.save()
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
    return result# here's where I'll put the populating functions