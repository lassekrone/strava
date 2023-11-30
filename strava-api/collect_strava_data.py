from datetime import datetime
import json
import os
import time
from typing import Dict, List, Tuple
import requests
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import pandas as pd
import urllib3
from build_data_model import connect_postgres

# disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def connect_strava() -> Dict[str, str]:
    load_dotenv()
    # Initial settings
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    refresh_token = os.getenv("REFRESH_TOKEN")

    # Authentication
    auth_url = "https://www.strava.com/oauth/token"

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "f": "json",
    }
    print("Requesting Token...\n")
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()["access_token"]  # Save new token
    header = {"Authorization": "Bearer " + access_token}
    return header


def make_api_request(header: Dict[str, str], activity_num: int = 1) -> Dict[str, str]:
    param = {"per_page": 1, "page": activity_num}
    api_response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities", headers=header, params=param
    ).json()
    response_json = api_response[0]
    return response_json


def parse_api_output(response_json: dict):
    cols_to_extract = [
        "id",
        "name",
        "distance",
        "moving_time",
        "elapsed_time",
        "total_elevation_gain",
        "type",
        "workout_type",
        "location_country",
        "achievement_count",
        "kudos_count",
        "map",
        "start_latlng",
        "end_latlng",
        "comment_count",
        "athlete_count",
        "average_speed",
        "max_speed",
        "average_cadence",
        "average_temp",
        "average_heartrate",
        "max_heartrate",
    ]

    activity_data = {}
    for col in cols_to_extract:
        try:
            activity_data[col] = response_json[col]
        except KeyError:
            activity_data[col] = None
    try:
        start_date = datetime.strptime(
            response_json["start_date"], "%Y-%m-%dT%H:%M:%SZ"
        )
        activity_data["start_date"] = start_date
    except KeyError:
        activity_data["start_date"] = None

    print(activity_data)

    return activity_data


def collect_activities(last_updated: datetime) -> List:
    header = connect_strava()
    all_activities = []
    activity_num = 1

    while True:
        if activity_num % 75 == 0:
            print("Strava rate limit hit, sleeping for 15 minutes...")
            time.sleep(15 * 60)
        try:
            response_json = make_api_request(header, activity_num)
        except KeyError:
            print("Strava rate limit hit, sleeping for 15 minutes...")
            time.sleep(15 * 60)
            response_json = make_api_request(header, activity_num)
        date = datetime.strptime(response_json["start_date"], "%Y-%m-%dT%H:%M:%SZ")

        if date > last_updated:
            activity = parse_api_output(response_json)
            all_activities.append(activity)
            activity_num += 1
        else:
            break
    print(len(all_activities))
    return all_activities


def save_data_to_json(all_activities: List) -> str:
    todays_date = datetime.today().strftime("%Y_%m_%d")
    export_file_path = f"strava-api/strava_data/{todays_date}_export_file.json"
    with open(export_file_path, "w+") as fp:
        json.dump(all_activities, fp, indent=2, default=str)

    return export_file_path


def save_extraction_date_to_db(current_datetime: datetime) -> None:
    pg_conn = connect_postgres()
    update_last_query = """
        INSERT INTO last_extracted (LastUpdated)
        VALUES (%s);
        """
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute(update_last_query, (current_datetime,))
    pg_conn.commit()
    print("Extraction date added to Postgres Database!")


def get_date_of_last_extraction_date() -> Tuple[datetime, str]:
    """Get datetime of last time data was collected from Strava API"""
    pg_conn = connect_postgres()
    get_last_updated_query = """
        SELECT COALESCE(MAX(LastUpdated), '1900-01-01')
        FROM last_extracted;"""
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute(get_last_updated_query)
    result = pg_cursor.fetchone()
    print(result)
    print(type(result[0]))
    last_updated_warehouse = result[0]
    current_datetime = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
    return last_updated_warehouse, current_datetime


latest_update_date, current_datetime = get_date_of_last_extraction_date()
all_activities = collect_activities(latest_update_date)
if all_activities:
    save_data_to_json(all_activities)
    save_extraction_date_to_db(current_datetime)


# CAN BE USED TO GET LAP DATA PER ACTIVITY
# df = pd.json_normalize(all_activities)
# tmp = []
# ##### Get inidivudal activity data
# for index, row in df[:10].iterrows():
#         get_activity_url = "https://www.strava.com/api/v3/activities/{}/laps".format(row['id'])
#         my_activity = requests.get(get_activity_url, headers=header, params=param).json()
#         tmp.extend(my_activity)
# pd.json_normalize(tmp)
