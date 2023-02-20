import requests
import json
import time
from requests.auth import HTTPBasicAuth
import re

from bs4 import BeautifulSoup

nice = 3 # seconds to wait between calls
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

followers = False
switch = 6

# get list of purchased items
url = "https://bandcamp.com/api/fancollection/1/collection_items"
fan_id = 15221
token = f"{int(time.time())}::a::"
count = 1


if switch == 1:
    # get list of followers
    url = "https://bandcamp.com/api/fancollection/1/followers"
    token = f"{int(time.time())}:"

elif switch == 2:
    # get list of following artists/labels
    url = "https://bandcamp.com/api/fancollection/1/following_bands"
    token = f"{int(time.time())}:"

elif switch == 3:
    # get list of following fans
    url = "https://bandcamp.com/api/fancollection/1/following_fans"
    token = f"{int(time.time())}:"

elif switch == 4: # currently non-functional b/c we need an api key
    url = "https://bandcamp.com/api/band/3/discography"
    name = 3480860214

elif switch == 5:
    # get a band/label discography
    url = "https://ehua.bandcamp.com/music"

elif switch == 6:
    # get album info
    url = "https://ehua.bandcamp.com/album/clouds-ep"

elif switch == 7:
    # get track info
    url = "https://ehua.bandcamp.com/track/piume"

r = requests.get(url)

blob = {
    "fan_id": fan_id,
    "older_than_token": token,
    "count": count,    
}

#TODO 0 - 3, 4*, 6,7
if switch < 4:
    r = requests.post(url, data=json.dumps(blob))
    print(r.json())
elif switch == 4:
    blob = {
        "key": "Avk5OLqXfHGDHkvYFbTYtA",
        "name": name,
    }    
    r = requests.post(url, data=json.dumps(blob))
    print(r.json())
elif switch == 5:
    # get discography info
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    data_band = soup.find_all("script", attrs={"data-band":True})[0]['data-band']
    label_name = re.search(re.compile(r'\"name\":\"(.*?)\"'), data_band).group(1)
    label_base_url = re.search(re.compile(r'\"url\":\"(.*?)\"'), data_band).group(1)
    label_music_url = label_base_url + "/music"
    label_id = re.search(re.compile(r'\"id\":(.*?),'), data_band).group(1)
    label_img = re.search(re.compile(r'\"image\":{(.*?)}'), data_band).group(1)
    label_img_url = re.search(re.compile(r'\"url\":\"(.*?)\"'), label_img).group(1)
    print(label_name, label_base_url, label_music_url, label_id, label_img_url)

    # TODO: seems like this is not rendering b/c we are not "logged-in"
    # data_following = soup.find_all("script", attrs={'data-band-follow-info':True})
    # is_following?

    albums = soup.find_all("li",attrs={'data-item-id':True})
    for a in albums:                
        title = a.p.string.strip()
        data_item_id = a['data-item-id']
        img_url = a.img['src'] 
        album_url = label_base_url + a.a['href']
        print(title,data_item_id, album_url, img_url)
elif switch == 6:
    # get album info
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = soup.find_all("script", attrs={"data-band":True})[0]

    data_band = data['data-band']    
    data_tralbum = data['data-tralbum']
    data_follow = data['data-band-follow-info']

    release_date = re.search(re.compile(r'\"release_date\":\"(.*?)\"'), data_tralbum).group(1)
    print(release_date)
    label_id = re.search(re.compile(r'\"id\":(.*?),'), data_band).group(1)
    label_name = re.search(re.compile(r'\"name\":(.*?),'), data_band).group(1)
    label_url = soup.find_all("div",attrs={"class":"desktop-header"})[0].a['href']
    label_img_url = soup.find_all("img",attrs={"class":"band-photo"})[0]['src']
    print(label_id, label_name, label_url, label_img_url)

    album_id = re.search(re.compile(r'\"id\":(.*?),'), data_tralbum).group(1)
    album_title = re.search(re.compile(r'\"title\":(.*?),'), data_tralbum).group(1)
    album_url = re.findall(re.compile(r'\"url\":(.*?),'), data_tralbum)[-1]

    item_type = soup.find_all("meta", attrs={"name":"bc-page-properties"})[0]['content']
    item_type = re.search(re.compile(r'\"item_type\":\"(.*?)\"'), item_type).group(1)    
    print(album_id, album_title, album_url, item_type)
    
    artist_id = re.search(re.compile(r'\"band_id\":(.*?),'), data_tralbum).group(1)
    selling_artist_id = re.search(re.compile(r'\"selling_band_id\":(.*?),'), data_tralbum).group(1)
    label = re.search(re.compile(r'\"label\":\"(.*?)\"'), data_tralbum).group(1)
    album_artist = re.search(re.compile(r'\"artist\":\"(.*?)\"'), data_tralbum).group(1)
    album_img_url = soup.find_all("div",attrs={"id":"tralbumArt"})[0].img['src']

    print(artist_id, selling_artist_id, label, album_artist, album_img_url)

    trackinfo = json.loads(re.search(re.compile(r'\"trackinfo\":(\[.*?\])'), data_tralbum).group(1))
    for t in trackinfo:
        track_id = t['track_id']
        track_artist = t['artist']
        track_name = t['title']
        track_mp3 = t['file']['mp3-128']
        track_url = label_url + t['title_link']
        track_duration = t['duration']
        track_number = t['track_num']
        print(track_number, track_id, track_artist, track_name, track_mp3, track_url, track_duration)

    #bought_by
    bought_url = "https://ehua.bandcamp.com/api/tralbumcollectors/2/thumbs"
    tralbum_id = 1331088894
    token = f"{int(time.time())}::::"
    count = 1

    blob = {
        "tralbum_id": tralbum_id,
        "older_than_token": token,
        "count": count,
        "tralbum_type": item_type
    }
    bought_r = requests.post(bought_url, data=json.dumps(blob))
    bought_by = bought_r.json()
    print(bought_by)
    for buyer in bought_by['results']:
        buyer_id = buyer['fan_id']
        buyer_username = buyer['username']
        buyer_name = buyer['name']
        buyer_img_id = buyer['image_id']

        buyer_img_url = "https://f4.bcbits.com/img/" + str(buyer_img_id).zfill(10) + "_42.jpg"
        print(buyer_id, buyer_username, buyer_name, buyer_img_id, buyer_img_url)
    exit()    

    # TODO: can't determine is_owned? until "logged-in"  
      
    # TODO: is_pre_order?

    # TODO: digital_price

    # TODO: compilation?
        
    
    
    



else:
    r = requests.get(url)
    
    