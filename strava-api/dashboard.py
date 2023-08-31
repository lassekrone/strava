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
import branca.colormap as cm

def time_filter(df):
    year_list = df.index.year.unique()
    return st.sidebar.selectbox(label='Select year', options=list(year_list))

def find_activity(df):
    return st.sidebar.selectbox(label='Select activity', options=list(df['activity_name'].unique()))

def main():
    st.set_page_config(page_title='Strava Dashboard', page_icon='🏃‍♂️', layout='wide')
    # Title
    st.title("Strava Dashboard")

    # Read in data
    with open('data.json', 'r') as f:
        df = json.load(f)

    df = pd.json_normalize(df)
    df.index = pd.to_datetime(df['start_date_local']).values
    df['polyline_decoded'] = df['map.summary_polyline'].apply(polyline.decode)
    daily_distances = round(df['distance'].resample('D').sum() / 1000,2).fillna(0)
    df['activity_name'] = df['name'] + ' (' + df.index.strftime('%d-%m-%Y') + ')'
    df['kilometers'] = df['distance'] / 1000

    # Sidebar
    year = time_filter(df)
    activity = find_activity(df)
    
    # Header metrics
    #opts = df.index.year.unique()
    #option = st.selectbox(label='Select year', options=list(opts))
    yearly_distance = df[df.index.year == year]
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.metric(label='Total kilometers', value=f'{round(yearly_distance["kilometers"].sum(),2)}')
    with col2:
        st.metric(label='Total activities', value=f'{len(df[df.index.year == year])}')
    with col3:
        if len(yearly_distance) == 365:
            st.metric(label='Average weekly distance', value=f'{round(yearly_distance["kilometers"].sum() / 52,2)}')
        else:
            st.metric(label='Average weekly distance', value=f'{round(yearly_distance["kilometers"].sum() / datetime.datetime.today().isocalendar().week,2)}')
    
    # Display cal-heatmap
    fig = plt.figure(figsize=(12,8))
    ax = plt.subplot()
    ax.patch.set_alpha(0)
    cal = calmap.yearplot(daily_distances,ax=ax, year=year, cmap='YlGn')
    fig.colorbar(cal.get_children()[1], ax=ax, orientation='horizontal', pad=0.04, shrink=0.5)
    st.pyplot(fig, clear_figure=True, bbox_inches='tight')
    
    # Select activity type
    yearly_distance = yearly_distance[yearly_distance['activity_name'] == activity]

    # Display activity map
    lat = np.mean(yearly_distance['polyline_decoded'][0], axis=0)[0]
    lon = np.mean(yearly_distance['polyline_decoded'][0], axis=0)[1]

    # Display activity 
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label='Distance', value=f'{round(yearly_distance["kilometers"].sum(),2)} km')
    with col2:
        st.metric(label='Average speed', value=f'{round(yearly_distance["average_speed"].sum(),2)} min/km')
    with col3:
        st.metric(label='Elevation gain', value=f'{round(yearly_distance["total_elevation_gain"].sum(),2)} m')

    m = folium.Map(location=[lat,lon], zoom_start=13, tiles='OpenStreetMap')
    folium.PolyLine(
        yearly_distance['polyline_decoded'], color="green"
        ).add_to(m)
    folium.Marker(
        yearly_distance['start_latlng'][0], popup='Start', icon=folium.Icon(color='green', icon='play', size=(10,10)), tooltip='Start'
    ).add_to(m)
    folium.Marker(
        yearly_distance['end_latlng'][0], popup='End', icon=folium.Icon(color='red', icon='stop', size=(10,10)), tooltip='End'
    ).add_to(m)
    
    st_data = st_folium(m, width=1200, height=500)
    
        
    
if __name__ == '__main__':
    main()