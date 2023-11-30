import json
import pandas as pd
import numpy as np
import datetime
import streamlit as st
import calmap
import plotly as plt
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import polyline
import plotly.express as px
from build_data_model import connect_postgres


def time_filter(df):
    year_list = df.index.year.unique()
    return st.sidebar.selectbox(label="Select year", options=list(year_list))


def find_activity(df):
    return st.sidebar.selectbox(
        label="Select activity", options=list(df["activity_name"].unique())
    )


def sport_type(df):
    return st.sidebar.radio(
        label="Select sport type", options=list(["Run", "Ride", "Walk"])
    )


def main():
    st.set_page_config(page_title="Strava Dashboard", page_icon="🏃‍♂️", layout="wide")
    # Title
    st.title("Strava Dashboard")

    # Read in data
    # with open("strava-api/strava_data/2023_11_30_export_file.json", "r") as f:
    #     df = json.load(f)
    # df = pd.json_normalize(df)

    pg_conn = connect_postgres()
    df = pd.read_sql_query("SELECT * FROM strava_activities;", pg_conn)

    df.index = pd.to_datetime(df["start_date"]).values
    df["polyline_decoded"] = df["summary_polyline"].apply(polyline.decode)
    df["activity_name"] = df["name"] + " (" + df.index.strftime("%d-%m-%Y %H:%M") + ")"
    df["kilometers"] = df["distance"] / 1000
    df["min/km"] = df["moving_time"] / 60 / df["kilometers"]

    year = time_filter(df)
    sport = sport_type(df)

    # Header metrics
    yearly_distance = df[df.index.year == year]
    yearly_distance = yearly_distance[yearly_distance["type"] == sport]
    daily_distances = round(
        yearly_distance["distance"].resample("D").sum() / 1000, 2
    ).fillna(0)

    activity = find_activity(yearly_distance)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Total kilometers",
            value=f'{round(yearly_distance["kilometers"].sum(),2)}',
        )
    with col2:
        st.metric(
            label="Total activities",
            value=f"{len(yearly_distance[yearly_distance.index.year == year])}",
        )
    with col3:
        if len(yearly_distance) == 365:
            st.metric(
                label="Average weekly distance",
                value=f'{round(yearly_distance["kilometers"].sum() / 52,2)}',
            )
        else:
            st.metric(
                label="Average weekly distance",
                value=f'{round(yearly_distance["kilometers"].sum() / datetime.datetime.today().isocalendar().week,2)}',
            )

    # Display cal-heatmap
    fig = plt.figure(figsize=(12, 8))
    ax = plt.subplot()
    ax.patch.set_alpha(0)
    cal = calmap.yearplot(daily_distances, ax=ax, year=year, cmap="YlGn")
    fig.colorbar(
        cal.get_children()[1], ax=ax, orientation="horizontal", pad=0.04, shrink=0.5
    )
    st.pyplot(fig, clear_figure=True, bbox_inches="tight")

    # Display weekly progress last 12 weeks
    st.header("Weekly progress last 12 weeks")
    weekly_progress = yearly_distance["kilometers"].resample("W").sum()
    weekly_progress = weekly_progress[
        weekly_progress.index.isocalendar().week
        >= datetime.datetime.today().isocalendar().week - 11
    ]

    # create tmp df with last 12 weeks including next week
    tmp = (
        pd.Series(
            index=pd.date_range(
                start=datetime.datetime.today() - datetime.timedelta(weeks=11),
                end=datetime.datetime.today() + datetime.timedelta(days=7),
                freq="W",
            )
        )
        .resample("W")
        .sum()
        .fillna(0)
    )
    weekly_progress = weekly_progress + tmp

    fig = px.line(
        weekly_progress,
        x=weekly_progress.index.isocalendar().week,
        y=weekly_progress.values,
        labels={"x": "Week", "y": "Distance (km)"},
        markers=True,
    )
    fig.update_layout(
        xaxis=dict(
            tickmode="linear",
        )
    )
    fig.update_traces(fill="tozeroy")
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    # Select activity type
    yearly_distance = yearly_distance[yearly_distance["activity_name"] == activity]

    # Display activity map
    lat = np.mean(yearly_distance["polyline_decoded"][0], axis=0)[0]
    lon = np.mean(yearly_distance["polyline_decoded"][0], axis=0)[1]

    # Display activity
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Distance", value=f'{round(yearly_distance["kilometers"][0],2)} km'
        )
    with col2:
        st.metric(
            label="Average speed",
            value=f'{round(yearly_distance["min/km"][0],2)} min/km',
        )
    with col3:
        st.metric(
            label="Elevation gain",
            value=f'{round(yearly_distance["total_elevation_gain"][0],2)} m',
        )

    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="OpenStreetMap")
    folium.PolyLine(yearly_distance["polyline_decoded"], color="green").add_to(m)
    folium.Marker(
        yearly_distance[["start_lat", "start_lng"]].iloc[0].tolist(),
        popup="Start",
        icon=folium.Icon(color="green", icon="play", size=(10, 10)),
        tooltip="Start",
    ).add_to(m)
    folium.Marker(
        yearly_distance[["end_lat", "end_lng"]].iloc[0].tolist(),
        popup="End",
        icon=folium.Icon(color="red", icon="stop", size=(10, 10)),
        tooltip="End",
    ).add_to(m)

    st_data = st_folium(m, width=1200, height=500)


if __name__ == "__main__":
    main()
