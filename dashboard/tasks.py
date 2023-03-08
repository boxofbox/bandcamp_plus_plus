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
from profiles.models import Profile, Purchase, IgnoredProfile
from releases.models import Release, Track, LabelBand
from bins.models import NewFollowers, NewFollowingFans, NewFollowingLabelBands, RecentFanPurchase, RecentLabelBandRelease

HARD_CODED_COUNT_LIMIT = 3 # TODO UPDATE!
HARD_CODED_DEFAULT_DELAY_TIME = 1

ABORT = -1
OK = 0
INIT_ERROR = -2
ERROR = -3
ERROR404 = -404

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
            return ABORT
        result += i
        logger.info(f'current status: {i}')
        progress_recorder.set_progress(i + 1, seconds, description="myprogressdesc")
    log_completed()
    return result# here's where I'll put the populating functions


def standard_abort_progress_request(abortable_task, url, blob=None, delay=None, progress_recorder=None, progress=None, progress_max=None, message=""):    
    # ALWAYS! delay and check for abort, and log progress before a request
    if delay is None:
        delay = HARD_CODED_DEFAULT_DELAY_TIME
    time.sleep(delay)
    if abortable_task.is_aborted():
        log_aborted()
        return ABORT # abort code
    if None not in (progress_recorder, progress, progress_max):
        progress_recorder.set_progress(progress, progress_max, message)

    r = None
    if blob is None:
        r = requests.get(url)
    else:
        r = requests.post(url, data=json.dumps(blob))
    if r.status_code != requests.codes.ok:
        r.raise_for_status()
    
    return r


def update_following_fans_subtask(abortable_task, settings_obj, progress_recorder, seen, new_following_fan_ids,
                               FLAG_UPDATE_NEW_FOLLOWING_FANS, FLAG_UPDATE_OLD_FOLLOWING_FANS):
    
    url = "https://bandcamp.com/api/fancollection/1/following_fans" 
    base_profile_id = settings_obj.base_profile.id
    cur_process = {base_profile_id:settings_obj.base_profile}
    old_profile_ids = set(Profile.objects.values_list('id', flat=True))
    ignored_profiles = set(IgnoredProfile.objects.values_list('id', flat=True))   
    
    depth = settings_obj.max_profile_depth    

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
                                                                      
            r = standard_abort_progress_request(abortable_task, url, blob, 
                                                settings_obj.delay_time, 
                                                progress_recorder, i, cur_block_size) # TODO update progress calcs
            if r == ABORT:
                return ABORT, seen, new_following_fan_ids
            
            following_fans = r.json()['followeers']                                       

            cached_followings = set()
            current_fan_id_set = set()

            preexisting_followings_ids = set(cur_process[id].following_fans.values_list('id', flat=True)) 
            
            for fan in following_fans:   
                fan_id = int(fan['fan_id'])
                
                if fan_id in ignored_profiles:
                    continue 

                current_fan_id_set.add(fan_id)

                if fan_id in seen:
                    cached_followings.add(fan_id)
                    continue
                elif not FLAG_UPDATE_OLD_FOLLOWING_FANS and fan_id in old_profile_ids:
                    cached_followings.add(fan_id)
                    continue                            
                elif not FLAG_UPDATE_NEW_FOLLOWING_FANS and fan_id not in old_profile_ids:
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

                    # add to the follower cache to update later
                    cached_followings.add(fan_id)

                    # mark as 'seen' to prevent circular traversals and store newly added for later binning
                    seen.add(fan_id)

                    # add to the dict for next level of depth processing
                    next_process[fan_id] = profile_obj

            if id == base_profile_id:                   
                new_following_fan_ids = current_fan_id_set - preexisting_followings_ids 

            # remove any new unfollows
            following_removal_set = preexisting_followings_ids - current_fan_id_set
            if len(following_removal_set) > 0:
                logger.warn(f"removing fan_id {id}'s following fans {following_removal_set}")
                cur_process[id].following_fans.remove(*Profile.objects.filter(id__in=following_removal_set))

            # process bulk following
            if len(cached_followings) > 0:
                cur_process[id].following_fans.add(*Profile.objects.filter(id__in=cached_followings))

            # save parent obj
            cur_process[id].save()

        cur_process = next_process
        depth -= 1
    return OK, seen, new_following_fan_ids

def update_fan_followers_subtask(abortable_task, settings_obj, progress_recorder, seen, new_follower_ids,
                               FLAG_UPDATE_NEW_FOLLOWING_FANS, FLAG_UPDATE_OLD_FOLLOWING_FANS):
    
    url = "https://bandcamp.com/api/fancollection/1/followers"

    old_profile_ids = set(Profile.objects.values_list('id', flat=True))      
    ignored_profiles = set(IgnoredProfile.objects.values_list('id', flat=True))   

    blob = {
        "fan_id": settings_obj.base_profile.id,
        "older_than_token": f"{int(time.time())}:",
        "count": HARD_CODED_COUNT_LIMIT,    
    }
    r = standard_abort_progress_request(abortable_task, url, blob, 
                                                settings_obj.delay_time) # TODO update progress calcs
    if r == ABORT:
        return ABORT, seen, new_follower_ids

    preexisting_followers_ids = set(settings_obj.base_profile.followers.values_list('id', flat=True))
    current_fan_id_set = set()

    followers = r.json()['followeers']
    for fan in followers:   
        fan_id = int(fan['fan_id'])

        if fan_id in ignored_profiles:
            continue

        current_fan_id_set.add(fan_id)

        if fan_id in seen:
            continue        
        elif not FLAG_UPDATE_OLD_FOLLOWING_FANS and fan_id in old_profile_ids:
            continue                            
        elif not FLAG_UPDATE_NEW_FOLLOWING_FANS and fan_id not in old_profile_ids:
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
            profile_obj.following_fans.add(settings_obj.base_profile)
            profile_obj.save()

            seen.add(fan_id)

    new_follower_ids = current_fan_id_set - preexisting_followers_ids

    follower_removal_set = preexisting_followers_ids - current_fan_id_set
    if len(follower_removal_set) > 0:
        logger.warn(f"removing fan_id {id}'s followers {follower_removal_set}")
        settings_obj.base_profile.followers.remove(*Profile.objects.filer(id__in=follower_removal_set))

    return OK, seen, new_follower_ids



def get_fan_network_id_set(settings_obj, FLAG_INCLUDE_BASE, FLAG_INCLUDE_NETWORK):
    # limit update to either base_profile, and/or network at depth
    fan_set = {}
    if FLAG_INCLUDE_BASE:
        fan_set = {settings_obj.base_profile_id}
    
    if FLAG_INCLUDE_NETWORK:
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
    
    return fan_set


def add_release(abortable_task, item_id, item_url, delay, seen_releases, 
                existing_labelband_ids, old_release_ids, 
                old_release_ids_added_from_tracks, new_added_release_ids):
    
    # pull album/track page info:           
    r = standard_abort_progress_request(abortable_task, item_url,  
                                        delay=delay) # TODO update progress calcs
    if r == ABORT:
        return ABORT

    soup = BeautifulSoup(r.text, 'html.parser')
    data = soup.find_all("script", attrs={"data-band":True})[0]  
    
    data_embed = json.loads(data['data-embed'])
    data_tralbum = json.loads(data['data-tralbum'])

    item_subclass = json.loads(soup.find_all("meta", attrs={"name":"bc-page-properties"})[0]['content'])['item_type']

    item_title = None
    if item_subclass == 't':
        item_title = data_tralbum['current']['title']
    else:
        item_title = data_embed['album_title']
    
    item_img_url = soup.find_all("div", attrs={"id":"tralbumArt"})[0].img['src']
    item_img_id = int(item_img_url.split("/")[-1].split("_")[0][1:])
    item_last_viewed_as_preorder = data_tralbum['album_is_preorder']
    item_artist_id = int(data_tralbum['current']['band_id'])
    item_artist_name = album_artist = data_embed['artist']
    item_selling_artist_id = int(data_tralbum['current']['selling_band_id'])

    logger.info(f"PROCESSING {item_artist_name} - {item_title}: {item_url}")

    # pricing & physical only checks
    digital_items = soup.find_all("li", attrs={"class":"buyItem digital"})
    item_default_price = "NO DIGITAL"
    if len(digital_items) > 0:        
        price_div = digital_items[0].find_all("span", attrs={"class":"nobreak"})
        if len(price_div) > 0:
            currency = soup.find_all("script",attrs={"data-band-currency":True})[0]['data-band-currency']
            item_default_price = price_div[0].find_all("span",attrs={"class":"base-text-color"})[0].text + " " + currency
        else:
            item_default_price = "FREE"

    album_id = None
    if data_embed.get('album_embed_data', None) is not None:
        album_id = data_embed['album_embed_data']['tralbum_param']['value']

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
            album_artist_img_url = album_artist_img_url_list[0]['src']                                                            
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
        elif old_release_ids is not None and album_id not in old_release_ids and album_id not in old_release_ids_added_from_tracks:
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

        if item_id in old_release_ids_added_from_tracks:
            old_release_ids_added_from_tracks.remove(item_id)

        release = album

        label_url = soup.find_all("div",attrs={"id":"name-section"})[0].h3.span.a['href']

        # populate tracks
        for t in data_tralbum['trackinfo']:
            track_id = int(t['track_id'])
            if track_id in seen_releases:
                continue
            # TODO: potentially flag here to select fewer tracks to update?
            else:
                track, _ = Track.objects.get_or_create(id=track_id)
                track.album = album
                track_file = t['file']
                if track_file is not None:
                    track.mp3 = t['file']['mp3-128']
                track.duration = float(t['duration'])
                track.track_number = int(t['track_num'])
                track.subclass = 't'
                track.title = t['title']
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
        return ERROR
    
    seen_releases.add(item_id)
    new_added_release_ids.add(item_id)

    return release


def update_purchases_subtask(abortable_task, settings_obj, progress_recorder, seen,
                     FLAG_UPDATE_BASE_PURCHASES, FLAG_UPDATE_FAN_PURCHASES,
                     FLAG_UPDATE_OLD_PURCHASES, FLAG_UPDATE_NEW_PURCHASES,
                     FLAG_UPDATE_OLD_PREORDERS, FLAG_UPDATE_OLD_NODIGITAL):
    
    url = "https://bandcamp.com/api/fancollection/1/collection_items"
    
    old_release_ids = set(Release.objects.values_list('id', flat=True)) # TODO performance tuning opportunity, maybe delete/cleanup after use?

    old_preorder_ids = None
    if not FLAG_UPDATE_OLD_PURCHASES and FLAG_UPDATE_OLD_PREORDERS:
        old_preorder_ids = set(Release.objects.filter(last_viewed_as_preorder=True).values_list('id', flat=True))

    old_nodigital_ids = None
    if not FLAG_UPDATE_OLD_PURCHASES and FLAG_UPDATE_OLD_NODIGITAL:
        old_nodigital_ids = set(Release.objects.filter(price="NO DIGITAL").values_list('id', flat=True))
    
    existing_labelband_ids = set(LabelBand.objects.values_list('id', flat=True)) # TODO performance tuning opportunity

    fan_set = get_fan_network_id_set(settings_obj, FLAG_UPDATE_BASE_PURCHASES, FLAG_UPDATE_FAN_PURCHASES)
    n_fans = len(fan_set)
    logger.info(f'current status: running update_purchases for {n_fans} users')
       
    old_release_ids_added_from_tracks = set()
    new_added_release_ids = set()

    for i, fan_id in enumerate(fan_set):
        cur_profile = Profile.objects.get(id=fan_id)                    
        # get the fan's purchases
        blob = {
            "fan_id": fan_id,
            "older_than_token": f"{int(time.time())}::a::",
            "count": HARD_CODED_COUNT_LIMIT,                      
        }

        r = standard_abort_progress_request(abortable_task, url, blob, 
                                                settings_obj.delay_time, 
                                                progress_recorder, i, n_fans) # TODO update progress calcs
        if r == ABORT:
            return ABORT, seen
        
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
            elif not FLAG_UPDATE_OLD_PURCHASES and FLAG_UPDATE_OLD_PREORDERS and item_id in old_preorder_ids:
                pass # We want to go ahead and process this one
            elif not FLAG_UPDATE_OLD_PURCHASES and FLAG_UPDATE_OLD_NODIGITAL and item_id in old_nodigital_ids:
                pass # We want to go ahead and process this one
            elif not FLAG_UPDATE_OLD_PURCHASES and item_id in old_release_ids:
                # Associate purchase
                purchase, created = Purchase.objects.get_or_create(profile=cur_profile, release=Release.objects.get(id=item_id))
                if created:
                    purchase.date = bcdate_to_datetime(item['purchased'])
                    purchase.save()
                continue                            
            elif not FLAG_UPDATE_NEW_PURCHASES and item_id not in old_release_ids:
                seen.add(item_id) # ignore it b/c it's NEW and don't add the purchase b/c we won't be creating the associated db entry
                continue 
            
            release = add_release(abortable_task, item_id, item['item_url'], settings_obj.delay_time, seen, 
                existing_labelband_ids, old_release_ids, old_release_ids_added_from_tracks, new_added_release_ids)
            if release == ABORT:
                return ABORT, seen - old_release_ids_added_from_tracks
            elif release == ERROR:
                return ERROR, seen - old_release_ids_added_from_tracks

            # Associate purchase
            purchase, created = Purchase.objects.get_or_create(profile=cur_profile, release=release)
            if created:
                purchase.date = bcdate_to_datetime(item['purchased'])
                purchase.save()

    return OK, seen - old_release_ids_added_from_tracks


def update_labelbands_subtask(abortable_task, settings_obj, progress_recorder, seen_releases, new_following_labelband_ids,
                              FLAG_UPDATE_BASE_LABELBANDS, FLAG_UPDATE_FAN_LABELBANDS,
                              FLAG_UPDATE_OLD_DISCOGRAPHY, FLAG_UPDATE_NEW_DISCOGRAPHY,
                              FLAG_UPDATE_OLD_DISCOG_PREORDERS, FLAG_UPDATE_OLD_DISCOG_NODIGITAL):
    
    old_release_ids = set(Release.objects.values_list('id', flat=True)) # TODO performance tuning opportunity

    old_preorder_ids = None
    if not FLAG_UPDATE_OLD_DISCOGRAPHY and FLAG_UPDATE_OLD_DISCOG_PREORDERS:
        old_preorder_ids = set(Release.objects.filter(last_viewed_as_preorder=True).values_list('id', flat=True))

    old_nodigital_ids = None
    if not FLAG_UPDATE_OLD_DISCOGRAPHY and FLAG_UPDATE_OLD_DISCOG_NODIGITAL:
        old_nodigital_ids = set(Release.objects.filter(price="NO DIGITAL").values_list('id', flat=True))
    
    existing_labelband_ids = set(LabelBand.objects.values_list('id', flat=True)) # TODO performance tuning opportunity    
    
    # limit update to either base_profile, and/or network at depth
    fan_set = get_fan_network_id_set(settings_obj, FLAG_UPDATE_BASE_LABELBANDS, FLAG_UPDATE_FAN_LABELBANDS)
    n_fans = len(fan_set)    
    logger.info(f'current status: running update_labelsbands for {n_fans} users')

    seen_bands = set()   
    old_release_ids_added_from_tracks = set()
    new_added_release_ids = set() 

    base_profile_id = settings_obj.base_profile.id

    for i, fan_id in enumerate(fan_set):      
                
        url = "https://bandcamp.com/api/fancollection/1/following_bands"                    
        blob = {
            "fan_id": fan_id,
            "older_than_token": f"{int(time.time())}:",
            "count": HARD_CODED_COUNT_LIMIT,    
        }
        
        r = standard_abort_progress_request(abortable_task, url, blob, 
                                                settings_obj.delay_time, 
                                                progress_recorder, i, n_fans) # TODO update progress calcs
        if r == ABORT:
            return ABORT, new_following_labelband_ids
        
        following_labelbands = r.json()['followeers']
                
        current_labelband_id_set = set()

        current_profile = Profile.objects.get(id=fan_id)

        preexisting_followings_ids = set(current_profile.following_labelbands.values_list('id',flat=True))
        
        
        for j, lb in enumerate(following_labelbands):            
            band_id = int(lb['band_id'])

            current_labelband_id_set.add(band_id)

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

                # PROCESS DISCOGRAPHY
                r = standard_abort_progress_request(abortable_task, labelband.url + "/music", 
                                                delay=settings_obj.delay_time ) # TODO update progress calcs
                if r == ABORT:
                    return ABORT, new_following_labelband_ids
                
                # list for comparing to existing list of releases (possibly from selling_artist)
                existing_releases = set(labelband.releases.values_list('id', flat=True)) | set(labelband.selling_releases.values_list('id', flat=True))
                                
                soup_discog = BeautifulSoup(r.text, 'html.parser')
                
                releases = soup_discog.find_all("li",attrs={'data-item-id':True})
                for k, rl in enumerate(releases):
                    item_id = int(rl['data-item-id'][6:])

                    if item_id in seen_releases:                        
                        continue
                    elif not FLAG_UPDATE_OLD_DISCOGRAPHY and FLAG_UPDATE_OLD_DISCOG_PREORDERS and item_id in old_preorder_ids:
                        pass # We want to go ahead and process this one
                    elif not FLAG_UPDATE_OLD_DISCOGRAPHY and FLAG_UPDATE_OLD_DISCOG_NODIGITAL and item_id in old_nodigital_ids:
                        pass # We want to go ahead and process this one
                    elif not FLAG_UPDATE_OLD_DISCOGRAPHY and item_id in old_release_ids:
                        continue                            
                    elif not FLAG_UPDATE_NEW_DISCOGRAPHY and item_id not in old_release_ids:
                        seen_releases.add(item_id) # ignore it b/c it's NEW and don't add the purchase b/c we won't be creating the associated db entry
                        continue 
                    
                    release = add_release(abortable_task, item_id, labelband.url + rl.a['href'], settings_obj.delay_time, seen_releases, 
                        existing_labelband_ids, old_release_ids, old_release_ids_added_from_tracks, new_added_release_ids)
                    if release == ABORT:
                        return ABORT, new_following_labelband_ids
                    elif release == ERROR:
                        return ERROR, new_following_labelband_ids
            
            if fan_id == base_profile_id:
                new_following_labelband_ids = current_labelband_id_set - preexisting_followings_ids
                
            # remove any new unfollows
            following_removal_set = preexisting_followings_ids - current_labelband_id_set
            if len(following_removal_set) > 0:
                logger.warn(f"removing fan_id {fan_id}'s following labelbands {following_removal_set}")
                current_profile.following_labelbands.remove(*LabelBand.objects.filter(id__in=following_removal_set)) 

            # process bulk following
            if len(current_labelband_id_set) > 0:
                current_profile.following_labelbands.add(*LabelBand.objects.filter(id__in=current_labelband_id_set))

            # save parent obj
            current_profile.save()

    return OK, new_following_labelband_ids


@shared_task(bind=True, base=AbortableTask)
def main_update_task(self, flags):
    # process flags    
    FLAG_UPDATE_FOLLOWING_FANS = flags.get("update_following_fans", False)
    FLAG_UPDATE_FOLLOWERS = flags.get("update_followers", False)
    FLAG_UPDATE_OLD_FOLLOWING_FANS = flags.get("update_profile_new", False)
    FLAG_UPDATE_NEW_FOLLOWING_FANS = flags.get("update_profile_old", False)

    FLAG_UPDATE_BASE_PURCHASES = flags.get("update_base_purchases", False)
    FLAG_UPDATE_FAN_PURCHASES = flags.get("update_fanpurchases", False)
    FLAG_UPDATE_OLD_PURCHASES = flags.get("update_purchases_old", False)
    FLAG_UPDATE_NEW_PURCHASES = flags.get("update_purchases_new", False)
    FLAG_UPDATE_OLD_PREORDERS = flags.get("update_old_preorders", False)
    FLAG_UPDATE_OLD_NODIGITAL = flags.get("update_old_nodigital", False)
    
    FLAG_UPDATE_FAN_LABELBANDS = flags.get("update_fan_labelartists", False)
    FLAG_UPDATE_BASE_LABELBANDS = flags.get("update_base_labelartists", False)
    FLAG_UPDATE_OLD_DISCOGRAPHY = flags.get("update_labelartists_old", False)
    FLAG_UPDATE_NEW_DISCOGRAPHY = flags.get("update_labelartists_new", False)
    FLAG_UPDATE_OLD_DISCOG_PREORDERS = flags.get("update_old_labelartists_preorders", False)
    FLAG_UPDATE_OLD_DISCOG_NODIGITAL = flags.get("update_old_labelartists_nodigital", False)

    FLAG_UPDATE_RELEASEOWNERS = flags.get("update_releaseowners", False)    

    # init
    if DashboardSettings.objects.count() >= 0:
        settings_obj = DashboardSettings.objects.get(lock='X')                
        if settings_obj.base_profile is not None:            
            progress_recorder = WebSocketProgressRecorder(self)
            progress_recorder.set_progress(0.0000001, 100, description="init")
        
            seen_profile_ids = set()
            seen_release_ids = set()
            
            new_following_fan_ids = set()
            new_follower_ids = set()
            new_following_labelband_ids = set()           

            abort_state = False
            if FLAG_UPDATE_FOLLOWING_FANS:
                status, seen_profile_ids, new_following_fan_ids = update_following_fans_subtask(self, settings_obj, progress_recorder, seen_profile_ids,
                               new_following_fan_ids, FLAG_UPDATE_NEW_FOLLOWING_FANS, FLAG_UPDATE_OLD_FOLLOWING_FANS)
                if status == ABORT:
                    abort_state = True
                
            if not abort_state and FLAG_UPDATE_FOLLOWERS:
                status, seen_profile_ids, new_follower_ids = update_fan_followers_subtask(self, settings_obj, progress_recorder, seen_profile_ids,
                               new_follower_ids, FLAG_UPDATE_NEW_FOLLOWING_FANS, FLAG_UPDATE_OLD_FOLLOWING_FANS)
                if status == ABORT:
                    return ABORT
            
            if not abort_state and (FLAG_UPDATE_BASE_PURCHASES or FLAG_UPDATE_FAN_PURCHASES):
                status, seen_release_ids = update_purchases_subtask(self, settings_obj, progress_recorder, seen_release_ids, 
                     FLAG_UPDATE_BASE_PURCHASES, FLAG_UPDATE_FAN_PURCHASES,
                     FLAG_UPDATE_OLD_PURCHASES, FLAG_UPDATE_NEW_PURCHASES,
                     FLAG_UPDATE_OLD_PREORDERS, FLAG_UPDATE_OLD_NODIGITAL)                
                if status == ABORT:
                    abort_state = True
                elif status == ERROR:
                    abort_state = True
            
            if not abort_state and (FLAG_UPDATE_BASE_LABELBANDS or FLAG_UPDATE_FAN_LABELBANDS):                
                status, new_following_labelband_ids = update_labelbands_subtask(self, settings_obj, progress_recorder, seen_release_ids,
                              new_following_labelband_ids, FLAG_UPDATE_BASE_LABELBANDS, FLAG_UPDATE_FAN_LABELBANDS,
                              FLAG_UPDATE_OLD_DISCOGRAPHY, FLAG_UPDATE_NEW_DISCOGRAPHY,
                              FLAG_UPDATE_OLD_DISCOG_PREORDERS, FLAG_UPDATE_OLD_DISCOG_NODIGITAL)              
                if status == ABORT:
                    abort_state = True
                elif status == ERROR:
                    abort_state = True
        
            if not abort_state and FLAG_UPDATE_RELEASEOWNERS:
                pass # TODO

            # UPDATE BINS!

            log_completed() # TODO individual subtask completed logs
            return OK
        
    return INIT_ERROR