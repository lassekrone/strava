CREATE TABLE IF NOT EXISTS strava_activities(
    id BIGINT,
    name VARCHAR(255),
    distance FLOAT,
    moving_time INTEGER,
    elapsed_time INTEGER,
    total_elevation_gain FLOAT,
    type VARCHAR(255),
    workout_type VARCHAR(255),
    location_country VARCHAR(255),
    achievement_count INTEGER,
    kudos_count INTEGER,
    summary_polyline TEXT,
    start_lat FLOAT,
    start_lng FLOAT,
    end_lat FLOAT,
    end_lng FLOAT,
    comment_count INTEGER,
    athlete_count INTEGER,
    average_speed FLOAT,
    max_speed FLOAT,
    average_cadence FLOAT,
    average_temp INTEGER,
    average_heartrate INTEGER,
    max_heartrate INTEGER,
    start_date TIMESTAMP
);