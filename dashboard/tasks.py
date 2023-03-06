import time
from celery import shared_task
from celery.contrib.abortable import AbortableTask
from celery_progress.websockets.backend import WebSocketProgressRecorder
from celery.utils.log import get_task_logger
import datetime
import requests
import json
from bs4 import BeautifulSoup

from .models import DashboardSettings
from profiles.models import Profile, Purchase
from releases.models import Release, Track, LabelBand

HARD_CODED_COUNT_LIMIT = 3 # TODO UPDATE!

logger = get_task_logger(__name__)

def log_completed():
    settings_obj, _ = DashboardSettings.objects.get_or_create(lock='X')        
    settings_obj.main_update_last_completed = datetime.datetime.utcnow()
    settings_obj.save()
    print("(^*)^*^)*^)*^)*^)*^ LOGGING COMPLETED")

def log_aborted():
    print("(^*)^*^)*^)*^)*^)*^ LOGGING ABORTED")

MONTH_MAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12 }

def bcdate_to_datetime(bcdate):
    bcdate_split = bcdate.split(" ")
    bctime_split = bcdate_split[3].split(":")
    return datetime.datetime(int(bcdate_split[2]),MONTH_MAP[bcdate_split[1]],int(bcdate_split[0]),
                             int(bctime_split[0]), int(bctime_split[1]), int(bctime_split[2]), tzinfo=datetime.timezone.utc)

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
# # TODO: recalc progress
# TODO better specification of NEW vs OLD (consider old profile's new purchases?)
    # for now we assume the NEW vs OLD uniquely applies to each level
    # e.g., it will update NEW purchases for all profiles in the database 
# TODO: update pre-orders 
# TODO: check request statuses
# TODO:
#   fan following labels/bands??? 
# TODO: followers?
# TODO:
    # a way to flesh out partially track'd albums
# TODO:
# change wording of last completed run

@shared_task(bind=True, base=AbortableTask)
def main_update_task(self, flags):
    FLAG_UPDATE_OLD = flags.get("update_old", False)
    FLAG_UPDATE_NEW = flags.get("update_new", False)
    FLAG_UPDATE_PROFILES = flags.get("update_profiles",False)
    FLAG_UPDATE_PURCHASES = flags.get("update_purchases", False)
    FLAG_UPDATE_FAN_PURCHASES = flags.get("update_fanpurchases", False)
    FLAG_UPDATE_LABELBANDS = flags.get("update_labelartists", False)
    FLAG_UPDATE_FAN_LABELBANDS = flags.get("update_fanlabelartists", False)
    FLAG_UPDATE_RELEASEOWNERS = flags.get("update_releaseowners", False)

    if DashboardSettings.objects.count() >= 0:
        progress_recorder = WebSocketProgressRecorder(self)
        
        settings_obj = DashboardSettings.objects.get(lock='X')
        
        
        if settings_obj.base_profile is not None:
            base_profile_id = settings_obj.base_profile.id
            delay = settings_obj.delay_time

            if FLAG_UPDATE_PROFILES:                
                url = "https://bandcamp.com/api/fancollection/1/following_fans"
                seen = set()
                cur_process = {base_profile_id:settings_obj.base_profile}
                old_profile_ids = set(Profile.objects.values_list('id', flat=True))
                new_added_profile_ids = set()
                
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
                        time.sleep(delay)
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
                            elif not FLAG_UPDATE_OLD and fan_id in old_profile_ids:
                                cached_followers.add(fan_id)
                                continue                            
                            elif not FLAG_UPDATE_NEW and fan_id not in old_profile_ids:
                                seen.add(fan_id) # ignore it b/c it's NEW
                                continue                       
                            else:                                   
                                profile_obj, _ = Profile.objects.get_or_create(id=fan_id)
                                profile_obj.username = fan['trackpipe_url'].split("/")[-1]
                                profile_obj.name = fan['name']
                                if fan['image_id'] is None:
                                    fan_img_id = 0
                                else:
                                    fan_img_id = int(fan['image_id'])
                                profile_obj.img_id = fan_img_id
                                profile_obj.save()

                                # add to the follower
                                cur_process[id].following_fans.add(profile_obj)

                                # mark as 'seen' to prevent circular traversals and store newly added for later binning
                                seen.add(fan_id)
                                new_added_profile_ids.add(fan_id)

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

            if FLAG_UPDATE_PURCHASES or FLAG_UPDATE_FAN_PURCHASES:
                url = "https://bandcamp.com/api/fancollection/1/collection_items"
                seen = set()
                old_release_ids = set(Release.objects.values_list('id', flat=True)) # TODO this is bad
                old_release_ids_added_from_tracks = set()
                new_added_release_ids = set()
                existing_labelband_ids = set(LabelBand.objects.values_list('id', flat=True)) # TODO this is bad

                # limit update to either base_profile, and/or network at depth
                fan_set = {}
                if FLAG_UPDATE_PURCHASES:
                    fan_set = {base_profile_id}
                
                if FLAG_UPDATE_FAN_PURCHASES:
                    depth = settings_obj.max_profile_depth
                    fans_seen = set()
                    cur_process = {settings_obj.base_profile}
                    next_process = set()
                    while (depth > 0):
                        for fan in cur_process:
                            if fan.id in fans_seen:
                                continue
                            following_fans = fan.following_fans.all()
                            fan_set |= set(following_fans.values_list('id', flat=True))
                            fans_seen.add(fan.id)
                        cur_process = next_process
                        depth -= 1 

                progress_max = 100
                progress_block_size = 0
                n_fans = len(fan_set)
                if n_fans > 0:
                    progress_block_size = progress_max / n_fans
                cur_progress_block = 0

                logger.info(f'current status: running update_purchases for {n_fans} users')

                for i, fan_id in enumerate(fan_set):
                    cur_profile = Profile.objects.get(id=fan_id)                    
                    # get the fan's purchases
                    blob = {
                        "fan_id": fan_id,
                        "older_than_token": f"{int(time.time())}::a::",
                        "count": HARD_CODED_COUNT_LIMIT,                      
                    }

                    # ALWAYS! delay and check for abort, and log progress before a request
                    time.sleep(delay)
                    if self.is_aborted():
                        log_aborted()
                        return -1 # abort code
                    progress_recorder.set_progress((progress_block_size * cur_progress_block) + (i / 1000), progress_max) # TODO

                    r = requests.post(url, data=json.dumps(blob))
                    if r.status_code != requests.codes.ok:
                        r.raise_for_status()
                    
                    items = r.json()['items']                    
                    
                    for j, item in enumerate(items):
                        item_id = item['item_id']                                                
                        if item_id in seen:
                            # Associate purchase
                            purchase, created = Purchase.objects.get_or_create(profile=cur_profile, release=Release.objects.get(id=item_id))
                            if created:
                                purchase.date = bcdate_to_datetime(item['purchased'])
                                purchase.save()
                            continue
                        elif not FLAG_UPDATE_OLD and item_id in old_release_ids:
                            # Associate purchase
                            purchase, created = Purchase.objects.get_or_create(profile=cur_profile, release=Release.objects.get(id=item_id))
                            if created:
                                purchase.date = bcdate_to_datetime(item['purchased'])
                                purchase.save()
                            continue                            
                        elif not FLAG_UPDATE_NEW and item_id not in old_release_ids:
                            seen.add(item_id) # ignore it b/c it's NEW
                            continue 
                        else:
                            item_subclass = item['tralbum_type']
                            item_title = item['item_title']
                            item_url = item['item_url']
                            item_img_id = int(item['item_art_id'])
                            item_last_viewed_as_preorder = item['is_preorder']
                            item_artist_id = int(item['band_id'])
                            item_artist_name = item['band_name']
                            logger.info(f"PROCESSING {item_artist_name} - {item_title}: {item_url}")

                            # pull album/track page info:
                            time.sleep(delay)
                            if self.is_aborted():
                                log_aborted()
                                return -1 # abort code                            
                            r = requests.get(item_url)
                            soup = BeautifulSoup(r.text, 'html.parser')
                            data = soup.find_all("script", attrs={"data-band":True})[0]  
                            
                            data_embed = json.loads(data['data-embed'])
                            data_tralbum = json.loads(data['data-tralbum'])
                        
                            item_selling_artist_id = int(data_tralbum['current']['selling_band_id'])

                            # pricing & physical only checks
                            digital_items = soup.find_all("li", attrs={"class":"buyItem digital"})
                            item_default_price = "NO DIGITAL"
                            if len(digital_items) > 0:        
                                price_div = digital_items[0].find_all("span", attrs={"class":"nobreak"})
                                if len(price_div) > 0:
                                    item_default_price = price_div[0].find_all("span",attrs={"class":"base-text-color"})[0].text + " " + item['currency']
                                else:
                                    item_default_price = "FREE"

                            album_id = None
                            if item['album_id'] is not None:
                                album_id = int(item['album_id'])

                            item_release_date = None
                            if data_tralbum['album_release_date'] is None:
                                item_release_date = bcdate_to_datetime(data_tralbum['current']['release_date'])
                            else:
                                item_release_date = bcdate_to_datetime(data_tralbum['album_release_date'])                                                     

                            # if album_artist doesn't exist, init  
                            album_artist = None                                  
                            if item_artist_id not in existing_labelband_ids:
                                logger.info(f"\tADDING {item_artist_name}")
                                album_artist, _ = LabelBand.objects.get_or_create(id=item_artist_id)
                                album_artist.name = item_artist_name
                                album_artist.url = soup.find_all("div",attrs={"id":"name-section"})[0].h3.span.a['href']                                
                                album_artist_img_url_list = soup.find_all("img",attrs={"class":"band-photo"})
                                if len(album_artist_img_url_list) == 0:
                                    album_artist.img_id = 0
                                else:
                                    album_artist_img_url = soup.find_all("img",attrs={"class":"band-photo"})[0]['src']                                                            
                                    album_artist.img_id = int(album_artist_img_url.split("/")[-1].split("_")[0])
                                album_artist.save()
                                existing_labelband_ids.add(item_artist_id)                                        
                            else:
                                album_artist = LabelBand.objects.get(id=item_artist_id)
                            
                            # if album_artist doesn't exist, init   
                            album_selling_artist = None                                 
                            if item_selling_artist_id not in existing_labelband_ids:
                                # NOTE: we currently have no way to get more seller info with our API
                                # NOTE: we also may have seen this before, because won't restrict updates 
                                #       from other paths (i.e., not adding to existing id list)
                                album_selling_artist, created = LabelBand.objects.get_or_create(id=item_selling_artist_id)
                                if created:
                                    album_selling_artist.save()
                            else:
                                album_selling_artist = LabelBand.objects.get(id=item_selling_artist_id)                            

                            release = None
                            if item_subclass == 't':
                                album = None
                                if album_id is None:
                                    # track is it's own album, so we only need to get or create album artist or selling
                                    pass                    
                                elif album_id not in old_release_ids and album_id not in old_release_ids_added_from_tracks:
                                    # we need to init the album
                                    album, _ = Release.objects.get_or_create(id=album_id)                                    
                                    album.subclass = 'a'
                                    album.title = data_embed['album_embed_data']['album_title']
                                    album.url = data_embed['album_embed_data']['linkback']                                    
                                    album.release_date = item_release_date
                                    album.last_viewed_as_preorder = data_tralbum['album_is_preorder']                                    
                                    album.artist_name = album_artist.name
                                    album.img_id = item_img_id # if defining via track, just use the track img
                                    album.artist = album_artist
                                    album.selling_artist = album_selling_artist
                                    album.save()                                                         
                                    old_release_ids_added_from_tracks.add(album_id)
                                else:
                                    album = Release.objects.get(id=album_id)

                                track, _ = Track.objects.get_or_create(id=item_id)
                                track.album = album
                                if data_tralbum['trackinfo'][0]['file'] is not None:
                                    track.mp3 = data_tralbum['trackinfo'][0]['file']['mp3-128']
                                track.duration = float(data_tralbum['trackinfo'][0]['duration'])
                                track_num = data_tralbum['current']['track_number']
                                if track_num is not None:
                                    track.track_number = int(track_num)
                                track.subclass = item_subclass
                                track.title = item_title                                
                                track.url = item_url
                                track.img_id = item_img_id
                                track.price = item_default_price
                                track.release_date = item_release_date
                                track.last_viewed_as_preorder = item_last_viewed_as_preorder
                                track.artist = album_artist
                                track.selling_artist = album_selling_artist
                                track.artist_name = data_tralbum['trackinfo'][0]['artist']
                                if track.artist_name is None:
                                    track.artist_name = item_artist_name
                                track.save()

                                release = track

                            elif item_subclass == 'a':

                                album, _ = Release.objects.get_or_create(id=item_id)
                                album.subclass = item_subclass
                                album.title = item_title
                                album.url = item_url
                                album.img_id = item_img_id
                                album.price = item_default_price
                                album.release_date = item_release_date
                                album.last_viewed_as_preorder = item_last_viewed_as_preorder
                                album.artist = album_artist
                                album.selling_artist = album_selling_artist
                                album.artist_name = item_artist_name
                                album.save()

                                release = album

                                label_url = soup.find_all("div",attrs={"id":"name-section"})[0].h3.span.a['href']

                                # populate tracks
                                for t in data_tralbum['trackinfo']:
                                    track_id = int(t['track_id'])
                                    if track_id in seen:
                                        continue
                                    elif not FLAG_UPDATE_OLD and track_id in old_release_ids:
                                        continue
                                    elif not FLAG_UPDATE_NEW and item_id not in old_release_ids:
                                        seen.add(item_id)
                                        continue
                                    else:
                                        track, _ = Track.objects.get_or_create(id=track_id)
                                        track.album = album
                                        track_file = t['file']
                                        if track_file is not None:
                                            track.mp3 = t['file']['mp3-128']
                                        track.duration = float(t['duration'])
                                        track.track_number = int(t['track_num'])
                                        track.subclass = 't'
                                        track.title = item_title
                                        title_link = t['title_link']
                                        if title_link is not None:
                                            track.url = label_url + t['title_link']
                                        track.img_id = item_img_id                                        
                                        track.release_date = item_release_date
                                        track.last_viewed_as_preorder = item_last_viewed_as_preorder

                                        track.artist_name = t['artist']
                                        if track.artist_name is None:
                                            track.artist_name = item_artist_name
                                        
                                        track.artist = album_artist
                                        track.selling_artist = album_selling_artist
                                        track.save()  

                                        # NOTE: since we can't update price, if we see it through track purchase
                                        # we will allow another update, and thus don't add to 'seen' yet

                            else:
                                logger.error(f"UNKNOWN SUBCLASS {item_subclass}; EXITING")
                                return -3
                            
                            seen.add(item_id)
                            new_added_release_ids.add(item_id)   

                            # Associate purchase
                            purchase, created = Purchase.objects.get_or_create(profile=cur_profile, release=release)
                            if created:
                                purchase.date = bcdate_to_datetime(item['purchased'])
                                purchase.save()

            if FLAG_UPDATE_LABELBANDS or FLAG_UPDATE_FAN_LABELBANDS:                
                # update labels i follow
                url = "https://bandcamp.com/api/fancollection/1/following_bands"
                seen_bands = set()
                seen_releases = set()
                
                # limit update to either base_profile, and/or network at depth
                # TODO encapsulate and cache this
                fan_set = {}
                if FLAG_UPDATE_LABELBANDS:
                    fan_set = {base_profile_id}
                
                if FLAG_UPDATE_FAN_LABELBANDS:
                    depth = settings_obj.max_profile_depth
                    fans_seen = set()
                    cur_process = {settings_obj.base_profile}
                    next_process = set()
                    while (depth > 0):
                        for fan in cur_process:
                            if fan.id in fans_seen:
                                continue
                            following_fans = fan.following_fans.all()
                            fan_set |= set(following_fans.values_list('id', flat=True))
                            fans_seen.add(fan.id)
                        cur_process = next_process
                        depth -= 1
                
                progress_max = 100
                progress_block_size = 0
                n_fans = len(fan_set)
                if n_fans > 0:
                    progress_block_size = progress_max / n_fans
                cur_progress_block = 0
                
                logger.info(f'current status: running update_labelsbands for {n_fans} users')

                for i, fan_id in enumerate(fan_set):      
                    following_labelbands_update_cache = set()         
                    url = "https://bandcamp.com/api/fancollection/1/following_bands"                    
                    blob = {
                        "fan_id": fan_id,
                        "older_than_token": f"{int(time.time())}:",
                        "count": HARD_CODED_COUNT_LIMIT,    
                    }
                    # ALWAYS! delay and check for abort, and log progress before a request
                    time.sleep(delay)
                    if self.is_aborted():
                        log_aborted()
                        return -1 # abort code
                    progress_recorder.set_progress((progress_block_size * cur_progress_block) + (i / 1000), progress_max) # TODO fix

                    r = requests.post(url, data=json.dumps(blob))
                    if r.status_code != requests.codes.ok:
                        r.raise_for_status()
                    
                    following_labelbands = r.json()['followeers']
                    
                    for j, lb in enumerate(following_labelbands):
                        
                        band_id = int(lb['band_id'])
                        following_labelbands_update_cache.add(band_id)

                        if band_id in seen_bands:
                            continue
                        else:
                            labelband, _ = LabelBand.objects.get_or_create(id=band_id)
                            # always update label band b/c could have been defined as selling_artist without info populated
                            labelband.name = lb['name']
                            labelband.url = "https://" + lb['url_hints']['subdomain'] + ".bandcamp.com"
                            if lb['image_id'] is None:
                                labelband.img_id = 0
                            else:
                                labelband.img_id = int(lb['image_id'])
                            labelband.save()

                            seen_bands.add(labelband)

                            # pull discography and update
                            # ALWAYS! delay and check for abort, and log progress before a request
                            time.sleep(delay)
                            if self.is_aborted():
                                log_aborted()
                                return -1 # abort code                            

                            r = requests.get(labelband.url)
                            if r.status_code != requests.codes.ok:
                                r.raise_for_status()
                            
                            # list for comparing to existing list of releases (possibly from selling_artist)
                            existing_releases = set(labelband.releases.values_list('id', flat=True)) | set(labelband.selling_releases.values_list('id', flat=True))
                            
                            # process discography
                            soup_discog = BeautifulSoup(r.text, 'html.parser')
                            
                            releases = soup_discog.find_all("li",attrs={'data-item-id':True})
                            for k, rl in enumerate(releases):
                                release_id = int(rl['data-item-id'][6:])

                                # TODO filter update for NEW/PREORDER!?!?
                                if not FLAG_UPDATE_OLD and release_id in existing_releases:
                                    continue
                                elif not FLAG_UPDATE_NEW and release_id not in existing_releases:
                                    continue
                                else:                                 
                                    # let's pull the album data and update
                                    pass # TODO Ooooooooooooooooooooooooooooo!!!!!!!!!!!!!!!!!!!!!!!!!!!!



                                
                                




                    # update following cache for cur_profile
                    cur_profile = Profile.objects.get(id=fan_id)
                    # TODO


                # TODO WORKING!!!!!!!!!!!!!!!!!!

            if FLAG_UPDATE_RELEASEOWNERS:
                # FROM ONLY THE BASE PROFILE PURCHASES!!!!!!!!!!!!!!!
                pass # TODO
            
            # PROCESS BINS!!!!!!!!!!! TODO

            log_completed()
            return 0 # success code
    return -2 # init error code
                