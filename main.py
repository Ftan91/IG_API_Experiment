from elasticsearch.client import IndicesClient
from elasticsearch import Elasticsearch
from pprint import pprint
from configurations import configurations

import requests
import facebook
import os

# make sure you have the 3 variables below set as env variable
# set within .bash_profile OR .zshenv within your $HOME directory
# to refresh use source ~/.bash_profile OR source ~/.zshenv
# to check, printenv in your terminal
short_lived_token = os.environ['IG_API_SHORT_TOKEN']
app_id = os.environ['APP_ID']
app_secret = os.environ['APP_SECRET']
version = 'v13.0'

# get the long lived token - should last 60 days
url = f'https://graph.facebook.com/{version}/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={short_lived_token} '
try:
    request = requests.get(url)
    time_left = request.json()['expires_in']/3600
    print(f'Long lived token remaining time: {round(time_left/24, 1)}')
    os.environ['IG_API_LONG_TOKEN'] = request.json()['access_token']
except KeyError:
    print('Short lived access token has expired. Defaulting to long lived access token.')

# sample request to graph api
graph = facebook.GraphAPI(access_token=os.environ['IG_API_LONG_TOKEN'])
test = graph.request('/17841404648986880?fields=media{media_type, like_count, insights.metric(reach)}')


es_client = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200, 'scheme': 'http'}],
                          http_auth=['elastic', 'changeme'])
es_index_client = IndicesClient(es_client)
index = 'ig_media'

try:
    es_index_client.create(index=index, body=configurations)
except Exception:
    print(f'Index {index} already exists')


# this is a list of all media that has been uploaded by user
media_data = test['media']['data']
for i in media_data:
    i.pop('insights')
    es_client.index(index=index, id=i['id'], body=i)
    print(f"Uploaded to ES ID: {i['id']}")
