import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

password = os.getenv("password")

# establishing the connection
conn = psycopg2.connect(
    database="stravadb",
    user="lassekrone",
    password=password,
    host="127.0.0.1",
    port="5432",
)
conn.autocommit = True

# Creating a cursor object using the cursor() method
cursor = conn.cursor()

# Preparing query to create a database
# sql = """CREATE database stravadb"""

# Creating a database
# cursor.execute(sql)
# print("Database created successfully........")

import json

with open("strava-api/data.json", "r") as f:
    json_data = f.read()

data = json.loads(json_data)


# create a function for inserting an activity into database
def insert_record(table_name, activity):
    # extract column names and values from activity
    columns = ", ".join(list(activity.keys()))
    values = str(tuple(activity.values()))
    # write SQL query
    insert_query = """INSERT INTO {} ({}) VALUES {};""".format(
        table_name, columns, values
    )
    return insert_query


# loop over activities
for activity in cleaned_activities:
    # insert activity into table
    cur.execute(insert_record("activities", activity))
    conn.commit()
# close connection to database
conn.close()


# executing queries to create table
# cursor.execute(
#     """
# CREATE TABLE Strava
# (
#     ID INT PRIMARY KEY NOT NULL,
#     athlete_id INT NOT NULL,
#     activity_name TEXT NOT NULL,
#     distance FLOAT NOT NULL,
#     moving_time INT NOT NULL,
#     type TEXT NOT NULL,
#     kudos_count INT NOT NULL
# )
# """
# )


# Closing the connection
conn.close()
