import json
import os
import requests
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
# disable warnings
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# Initial settings
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')

# Authentication
auth_url = 'https://www.strava.com/oauth/token'

payload = {
    'client_id': client_id,
    'client_secret': client_secret,
    'refresh_token': refresh_token,
    'grant_type': 'refresh_token',
    'f': 'json'
}

print('Requesting Token...\n')
res = requests.post(auth_url, data=payload, verify=False)
access_token = res.json()['access_token'] # Save new token
header = {'Authorization': 'Bearer ' + access_token}
url = 'https://www.strava.com/api/v3/athlete/activities'


request_page_num = 1
all_activities = []

while True:
    param = {'per_page': 200, 'page': request_page_num}
    data = requests.get(url, headers=header, params=param).json()
    print(len(data))
    if len(data) == 0:
        print('No more data found... Bye!')
        break
    if all_activities:
        print("Appending data... (page {})".format(request_page_num))
        all_activities.extend(data)
    else:
        all_activities = data

    request_page_num += 1

print(len(all_activities))
for count, activity in enumerate(all_activities):
    print(count, activity['name'])

# save data
with open('data.json', 'w') as f:
    json.dump(all_activities, f)
