from datetime import datetime
import psycopg2
from psycopg2 import sql
import os
import json
from dotenv import load_dotenv

load_dotenv()

with open("strava-api/strava_data/2023_11_30_export_file.json", "r") as f:
    data = json.load(f)


def connect_postgres():
    password = os.getenv("password")
    """Get Postgres info and connect to db."""
    database = os.getenv("database")
    user = os.getenv("user")
    host = os.getenv("host")
    port = os.getenv("port")

    conn = psycopg2.connect(
        database=database, user=user, password=password, host=host, port=port
    )
    conn.autocommit = True

    return conn


def create_db(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""CREATE database stravadb""")
        print("Database created successfully........")
    except Exception as e:
        return e
    connection.close()


def insert_data(cursor, data):
    for record in data:
        start_latlng = record.get("start_latlng", [None, None])
        end_latlng = record.get("end_latlng", [None, None])
        cursor.execute(
            """
            INSERT INTO strava_activities (
                id, name, distance, moving_time, elapsed_time,
                total_elevation_gain, type, workout_type, location_country,
                achievement_count, kudos_count, summary_polyline,
                start_lat, start_lng, end_lat, end_lng,
                comment_count, athlete_count, average_speed, max_speed,
                average_cadence, average_temp, average_heartrate, max_heartrate,
                start_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                record.get("id", None),
                record.get("name", None),
                record.get("distance", None),
                record.get("moving_time", None),
                record.get("elapsed_time", None),
                record.get("total_elevation_gain", None),
                record.get("type", None),
                record.get("workout_type", None),
                record.get("location_country", None),
                record.get("achievement_count", None),
                record.get("kudos_count", None),
                record.get("map", {}).get("summary_polyline", None),
                start_latlng[0] if start_latlng else None,
                start_latlng[1] if start_latlng else None,
                end_latlng[0] if end_latlng else None,
                end_latlng[1] if end_latlng else None,
                record.get("comment_count", None),
                record.get("athlete_count", None),
                record.get("average_speed", None),
                record.get("max_speed", None),
                record.get("average_cadence", None),
                record.get("average_temp", None),
                record.get("average_heartrate", None),
                record.get("max_heartrate", None),
                datetime.strptime(record.get("start_date", ""), "%Y-%m-%d %H:%M:%S"),
            ),
        )


def build_data_model(sql_script_path: str) -> None:
    """Execute sql query to build data model."""
    conn = connect_postgres()
    cursor = conn.cursor()
    sql_file = open(sql_script_path, "r")
    cursor.execute(sql_file.read())
    conn.commit()
    cursor.close()
    conn.close()


def update_database():
    conn = connect_postgres()
    cursor = conn.cursor()
    insert_data(cursor, data)
    conn.commit()
    cursor.close()
    conn.close()


sql_script_path = "strava-api/sql/build_data_model.sql"
sql_last_extracted_script_path = "strava-api/sql/last_extracted.sql"
build_data_model(sql_script_path)
update_database()
