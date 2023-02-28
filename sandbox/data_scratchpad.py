import requests
import json
import time
from bs4 import BeautifulSoup

nice = 3 # seconds to wait between calls
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
bought_url = "https://bandcamp.com/api/tralbumcollectors/2/thumbs"

fan_id = 15221
count = 10
switch = 1


if switch == -3:
    url = 'https://bandcamp.com/boxofbox'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = soup.find_all("div", attrs={"data-blob":True})[0]
    data_blob = json.loads(data['data-blob'])    
    print(data_blob['fan_data']['fan_id'],data_blob['fan_data']['username'],data_blob['fan_data']['name'],data_blob['fan_data']['photo']['image_id'])
    


elif switch == -2:
    # get list of purchased items
    url = "https://bandcamp.com/api/fancollection/1/collection_items"
    token = f"{int(time.time())}::a::" 
    blob = {
        "fan_id": "ab", #100002020202020020202,
        "older_than_token": token,
        "count": 1,    
    }   
    r = requests.post(url, data=json.dumps(blob)).json()      
    if r.get('error',False) is True:
        print("ERROR: ", r['error_message'])
        exit()
    items = r['items']
    print(items)

elif switch == -1:
    url = "https://bandcamp.com/boxofbox"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    text_404 = "Sorry, that something"
    is_404 = len(soup.find_all(lambda tag: tag.name == "h2" and text_404 in tag.text)) > 0

    print(is_404)

elif switch == 0:
    # get list of purchased items
    url = "https://bandcamp.com/api/fancollection/1/collection_items"
    token = f"{int(time.time())}::a::" 
    blob = {
        "fan_id": fan_id,
        "older_than_token": token,
        "count": count,    
    }   
    r = requests.post(url, data=json.dumps(blob))
    items = r.json()['items']
    for i in items:
        item_id = i['item_id']
        item_type = i['tralbum_type']
        item_band_id = i['band_id']
        item_band_name = i['band_name']
        item_band_url = i['band_url']
        item_purchased_date = i['purchased']
        item_also_collected_count = i['also_collected_count']
        item_title = i['item_title']
        item_url = i['item_url']
        item_img_url = i['item_art_url']
        item_album_id = i['album_id'] # BUG: can be None if a single track release
        item_album_title = i['album_title']
        print(item_id, item_type, item_band_id, item_band_name, item_band_url)
        print("\t", item_also_collected_count, item_title, item_url, item_img_url)
        print("\t", item_album_id, item_album_title)

elif switch == 1:
    # get list of followers
    url = "https://bandcamp.com/api/fancollection/1/followers"
    token = f"{int(time.time())}:"
    blob = {
        "fan_id": fan_id,
        "older_than_token": token,
        "count": count,    
    }
    r = requests.post(url, data=json.dumps(blob))
    followers = r.json()['followeers']
    for f in followers:
        fan_id = f['fan_id']
        fan_url = f['trackpipe_url']
        fan_name = f['name']
        image_id = f['image_id']
        fan_username = fan_url.split("/")[-1]
        print(fan_id,fan_name,fan_username,fan_url, image_id)
    
elif switch == 2:
    # get list of following artists/labels
    url = "https://bandcamp.com/api/fancollection/1/following_bands"
    token = f"{int(time.time())}:"
    blob = {
        "fan_id": fan_id,
        "older_than_token": token,
        "count": count,    
    }
    r = requests.post(url, data=json.dumps(blob))
    following_bands = r.json()['followeers']
    print(following_bands[0])
    for f in following_bands:
        band_id = f['band_id']
        band_img_id = f['image_id']
        band_img_url = "https://f4.bcbits.com/img/" + str(band_img_id).zfill(10) + "_41.jpg"        
        band_url = "https://" + f['url_hints']['subdomain'] + ".bandcamp.com"
        print("\tCUSTOM: ", f['url_hints']['custom_domain']) # BUG: TODO: need to double-check this e.g., https://music.businesscasual.biz/
        band_name = f['name']
        print(band_id, band_img_id, band_url, band_name, band_img_url)

elif switch == 3:
    # get list of following fans
    url = "https://bandcamp.com/api/fancollection/1/following_fans"
    token = f"{int(time.time())}:"
    blob = {
        "fan_id": fan_id,
        "older_than_token": token,
        "count": count,    
    }
    r = requests.post(url, data=json.dumps(blob))
    following_fans = r.json()['followeers']
    for f in following_fans:
        fan_id = f['fan_id']
        fan_url = f['trackpipe_url']
        fan_name = f['name']
        fan_username = fan_url.split("/")[-1]
        print(fan_id,fan_name,fan_username,fan_url)

elif switch == 4:
    # get discography info
    url = "https://ehua.bandcamp.com/music"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')    

    data_band = json.loads(soup.find_all("script", attrs={"data-band":True})[0]['data-band'])
    
    label_name = data_band['name']
    label_base_url = data_band['url']
    label_music_url = label_base_url + "/music"
    label_id = data_band['id']
    label_img_url = data_band['header_desktop']['image']['url']
    print(label_name, label_base_url, label_music_url, label_id, label_img_url)
    
    albums = soup.find_all("li",attrs={'data-item-id':True})
    for a in albums:                
        title = a.p.string.strip()
        data_item_id = a['data-item-id'][6:]
        img_url = a.img['src'] 
        album_url = label_base_url + a.a['href']
        print(title,data_item_id, album_url, img_url)
    
elif switch == 5:
    # album info    
    url = "https://sebastienforrester.bandcamp.com/album/orpheus-pipes-object-oriented-studies"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = soup.find_all("script", attrs={"data-band":True})[0]    
    
    data_band = json.loads(data['data-band'])
    data_embed = json.loads(data['data-embed'])
    data_tralbum = json.loads(data['data-tralbum'])
    data_follow = json.loads(data['data-band-follow-info'])    

    label_id = data_band['id']
    label_name = data_band['name']
    label_img_url = soup.find_all("img",attrs={"class":"band-photo"})[0]['src']
    label_url = soup.find_all("div",attrs={"id":"name-section"})[0].h3.span.a['href']
    print("LABEL: ",label_id, label_name, label_url, label_img_url)

    album_id = data_embed['tralbum_param']['value']
    album_title = data_embed['album_title']
    album_url = data_embed['linkback']
    album_artist = data_embed['artist']
    album_img_url = soup.find_all("div", attrs={"id":"tralbumArt"})[0].img['src']
    release_date = data_tralbum['album_release_date']
    item_type = json.loads(soup.find_all("meta", attrs={"name":"bc-page-properties"})[0]['content'])['item_type']       
    print("ALBUM: ", item_type, album_id, album_title, album_url, album_artist, album_img_url, release_date)

    artist_id = data_tralbum['current']['band_id']
    selling_artist_id = data_tralbum['current']['selling_band_id']  
    album_is_preorder =  data_tralbum['album_is_preorder']
    
    # pricing & physical only checks
    digital_items = soup.find_all("li", attrs={"class":"buyItem digital"})
    default_price = "NO DIGITAL"
    if len(digital_items) > 0:        
        price_div = digital_items[0].find_all("span", attrs={"class":"nobreak"})
        if len(price_div) > 0:
            default_price = price_div[0].find_all("span",attrs={"class":"base-text-color"})[0].text
        else:
            default_price = "FREE"

    currency = soup.find_all("script",attrs={"data-band-currency":True})[0]['data-band-currency']

    print("SELLING: ", artist_id, selling_artist_id, album_is_preorder, default_price, currency)

    for t in data_tralbum['trackinfo']:
        track_id = t['track_id']
        track_mp3 = None
        if t['file'] is not None:
            track_mp3 = t['file']['mp3-128']
        track_title = t['title']
        track_number = t['track_num']
        track_url = t['title_link']
        if track_url is not None:
            track_url = label_url + t['title_link']
        track_artist = t['artist']
        if track_artist is None:
            track_artist = album_artist            
        track_duration = t['duration']
        print(track_number, track_id, track_artist, track_title, track_duration, track_url, track_mp3)
    
    # BOUGHT BY      
    token = f"{int(time.time())}::::"
    count = 1

    blob = {
        "tralbum_id": album_id,
        "older_than_token": token,
        "count": count,
        "tralbum_type": item_type
    }

    bought_r = requests.post(bought_url, data=json.dumps(blob))
    bought_by = bought_r.json()
    for buyer in bought_by['results']:
        buyer_id = buyer['fan_id']
        buyer_username = buyer['username']
        buyer_name = buyer['name']
        buyer_img_id = buyer['image_id']

        buyer_img_url = "https://f4.bcbits.com/img/" + str(buyer_img_id).zfill(10) + "_42.jpg"
        print(buyer_id, buyer_username, buyer_name, buyer_img_id, buyer_img_url)   
        
elif switch == 6:
    # track info

    url = "https://twoshell.bandcamp.com/track/no-reply-1"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = soup.find_all("script", attrs={"data-band":True})[0]    
    
    data_band = json.loads(data['data-band'])
    data_embed = json.loads(data['data-embed'])
    data_tralbum = json.loads(data['data-tralbum'])
    data_follow = json.loads(data['data-band-follow-info'])
    
    label_id = data_band['id']
    label_name = data_band['name']
    label_img_url = soup.find_all("img",attrs={"class":"band-photo"})[0]['src']
    label_url = soup.find_all("div",attrs={"id":"name-section"})[0].h3.span.a['href']
    print("LABEL: ",label_id, label_name, label_url, label_img_url)

    album_id = data_embed['album_embed_data']['tralbum_param']['value']
    album_title = data_embed['album_embed_data']['album_title']
    album_url = data_embed['album_embed_data']['linkback']
    album_artist = data_embed['album_embed_data']['artist']
    album_img_url = soup.find_all("div", attrs={"id":"tralbumArt"})[0].img['src']
    release_date = data_tralbum['album_release_date']
    print("ALBUM: ",album_id, album_title, album_url, album_artist, album_img_url, release_date)

    item_type = json.loads(soup.find_all("meta", attrs={"name":"bc-page-properties"})[0]['content'])['item_type']       
    track_id = data_embed['tralbum_param']['value']
    track_title = data_tralbum['current']['title']
    track_number = data_tralbum['current']['track_number']
    track_url = data_tralbum['url']
    track_artist = data_tralbum['artist']
    print("TRACK: ", item_type, track_id, track_artist, track_title, track_number, track_url)

    track_mp3 = data_tralbum['trackinfo'][0]['file']
    if track_mp3 is not None:
        track_mp3 = track_mp3['mp3-128']
    track_duration = data_tralbum['trackinfo'][0]['duration']
    print(track_mp3, track_duration)

    artist_id = data_tralbum['current']['band_id']
    selling_artist_id = data_tralbum['current']['selling_band_id']  
    album_is_preorder =  data_tralbum['album_is_preorder']
    
    # pricing & physical only checks
    digital_items = soup.find_all("li", attrs={"class":"buyItem digital"})
    default_price = "NO DIGITAL"
    if len(digital_items) > 0:        
        price_div = digital_items[0].find_all("span", attrs={"class":"nobreak"})
        if len(price_div) > 0:
            default_price = price_div[0].find_all("span",attrs={"class":"base-text-color"})[0].text
        else:
            default_price = "FREE"

    currency = soup.find_all("script",attrs={"data-band-currency":True})[0]['data-band-currency']

    print("SELLING: ", artist_id, selling_artist_id, album_is_preorder, default_price, currency)

    # BOUGHT BY        
    token = f"{int(time.time())}::::"
    count = 1

    blob = {
        "tralbum_id": track_id,
        "older_than_token": token,
        "count": count,
        "tralbum_type": item_type
    }

    bought_r = requests.post(bought_url, data=json.dumps(blob))
    bought_by = bought_r.json()
    for buyer in bought_by['results']:
        buyer_id = buyer['fan_id']
        buyer_username = buyer['username']
        buyer_name = buyer['name']
        buyer_img_id = buyer['image_id']

        buyer_img_url = "https://f4.bcbits.com/img/" + str(buyer_img_id).zfill(10) + "_42.jpg"
        print(buyer_id, buyer_username, buyer_name, buyer_img_id, buyer_img_url)   