import time
from celery import shared_task
from celery.contrib.abortable import AbortableTask
from celery_progress.websockets.backend import WebSocketProgressRecorder
from celery.utils.log import get_task_logger
import datetime
import requests
import json

from .models import DashboardSettings
from profiles.models import Profile

HARD_CODED_COUNT_LIMIT = 3 # TODO UPDATE!

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


# TODO: update who they are following
# TODO: what about removing followings? if unfollowed later? 
# # TODO only update not new flag          
# TODO: log complete

@shared_task(bind=True, base=AbortableTask)
def main_update_task(self, flags):
    if DashboardSettings.objects.count() >= 0:
        progress_recorder = WebSocketProgressRecorder(self)
        
        settings_obj = DashboardSettings.objects.get(lock='X')
        delay = settings_obj.delay_time
        
        if settings_obj.base_profile is not None:
            if flags.get("update_profiles",False):                
                url = "https://bandcamp.com/api/fancollection/1/following_fans"
                seen = set()
                cur_process = {settings_obj.base_profile.id:settings_obj.base_profile}

                depth = settings_obj.max_profile_depth    

                progress_max = 100
                progress_block_size = 0
                if depth > 0:
                    progress_block_size = progress_max / depth
                cur_progress_block = 0

                logger.info(f'current status: running update_profiles at depth: {depth}')

                while (depth > 0):
                    next_process = dict()
                    cur_block_size = len(cur_process)
                    for i, id in enumerate(cur_process):                        
                        blob = {
                            "fan_id": id,
                            "older_than_token": f"{int(time.time())}:",
                            "count": HARD_CODED_COUNT_LIMIT,    
                        }                                                
                        
                        # ALWAYS! delay and check for abort, and log progress before a request
                        time.sleep(1)
                        if self.is_aborted():
                            log_aborted()
                            return -1 # abort code
                        progress_recorder.set_progress((progress_block_size * cur_progress_block) + (i / cur_block_size), progress_max)

                        r = requests.post(url, data=json.dumps(blob))
                        if r.status_code != requests.codes.ok:
                            r.raise_for_status()
                        
                        following_fans = r.json()['followeers']
                        cached_followers = set()
                        for fan in following_fans:   
                            fan_id = int(fan['fan_id'])
                            if fan_id in seen:
                                cached_followers.add(fan_id)
                                continue
                            else:                                    
                                
                                fan_name = fan['name']
                                fan_username = fan['trackpipe_url'].split("/")[-1]
                                if fan['image_id'] is None:
                                    fan_img_id = 0
                                else:
                                    fan_img_id = int(fan['image_id'])                                    
                                profile_obj, _ = Profile.objects.get_or_create(id=fan_id)
                                profile_obj.username = fan_username
                                profile_obj.name = fan_name
                                profile_obj.img_id = fan_img_id
                                profile_obj.save()

                                # add to the follower
                                cur_process[id].following_fans.add(profile_obj)

                                # mark as 'seen' to prevent circular traversals
                                seen.add(fan_id)

                                # add to the dict for next level of depth processing
                                next_process[fan_id] = profile_obj

                        # process cached followers
                        if len(cached_followers) > 0:
                            cur_process[id].following_fans.add(*Profile.objects.filter(id__in=cached_followers))

                        # save parent obj
                        cur_process[id].save()

                    cur_process = next_process
                    depth -= 1
                    cur_progress_block += 1


            return 0 # success code
    return -2 # init error code
                

    

"""
body.update_purchases = document.getElementById("update_purchases").checked;
body.update_fanpurchases = document.getElementById("update_fanpurchases").checked;
body.update_labelartists = document.getElementById("update_labelartists").checked;
body.update_releaseowners = document.getElementById("update_releaseowners").checked;
"""