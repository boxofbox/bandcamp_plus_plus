import requests
import json
import time

nice = 3 # seconds to wait between calls

followers = False
switch = 3

# get list of purchased items
url = "https://bandcamp.com/api/fancollection/1/collection_items"
fan_id = 15221
token = f"{int(time.time())}::a::"
count = 1


# get list of followers
if switch == 1:
    url = "https://bandcamp.com/api/fancollection/1/followers"
    token = f"{int(time.time())}:"
# get list of following artists/labels
elif switch == 2:
    url = "https://bandcamp.com/api/fancollection/1/following_bands"
    token = f"{int(time.time())}:"
# get list of following fans
elif switch == 3:
    url = "https://bandcamp.com/api/fancollection/1/following_fans"
    token = f"{int(time.time())}:"


r = requests.get(url)
blob = {
    "fan_id": fan_id,
    "older_than_token": token,
    "count": count,    
}

r = requests.post(url, data=json.dumps(blob))

print(r.json())







