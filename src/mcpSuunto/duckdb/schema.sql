CREATE TABLE IF NOT EXISTS activities (
    activity_id VARCHAR PRIMARY KEY,

    source_file VARCHAR NOT NULL,

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,

    sport VARCHAR NOT NULL,
    sub_sport VARCHAR,

    duration_seconds DOUBLE,
    elapsed_seconds DOUBLE,

    distance_m DOUBLE,

    ascent_m DOUBLE,
    descent_m DOUBLE,

    min_altitude_m DOUBLE,
    max_altitude_m DOUBLE,

    avg_heart_rate INTEGER,
    min_heart_rate INTEGER,
    max_heart_rate INTEGER,

    avg_speed_m_s DOUBLE,
    max_speed_m_s DOUBLE,

    calories INTEGER,

    avg_temperature_c DOUBLE,
    max_temperature_c DOUBLE,

    avg_cadence DOUBLE,
    max_cadence DOUBLE,

    avg_power_w DOUBLE,
    max_power_w DOUBLE,
    normalized_power_w DOUBLE,

    total_strides INTEGER,

    training_stress_score DOUBLE,
    intensity_factor DOUBLE,
    training_effect DOUBLE,

    recovery_time_seconds DOUBLE,
    peak_epoc DOUBLE,

    estimated_vo2_max DOUBLE,

    feeling INTEGER,
    avg_ngp_m_s DOUBLE,
    hills DOUBLE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS records (
    activity_id VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    latitude DOUBLE,
    longitude DOUBLE,

    distance_m DOUBLE,

    altitude_m DOUBLE,

    speed_m_s DOUBLE,

    heart_rate INTEGER,

    cadence DOUBLE,

    power_w DOUBLE,

    temperature_c DOUBLE,

    vertical_speed_m_s DOUBLE,
    ngp_m_s DOUBLE,
    grade_pct DOUBLE,

    PRIMARY KEY (activity_id, timestamp)
);

CREATE TABLE IF NOT EXISTS laps (
    lap_id BIGINT PRIMARY KEY,

    activity_id VARCHAR NOT NULL,

    start_time TIMESTAMP,
    end_time TIMESTAMP,

    duration_seconds DOUBLE,
    elapsed_seconds DOUBLE,

    event VARCHAR,
    event_type VARCHAR,
    lap_trigger VARCHAR,

    distance_m DOUBLE,

    ascent_m DOUBLE,
    descent_m DOUBLE,

    min_altitude_m DOUBLE,
    avg_altitude_m DOUBLE,
    max_altitude_m DOUBLE,

    min_heart_rate INTEGER,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,

    avg_speed_m_s DOUBLE,
    max_speed_m_s DOUBLE,

    avg_cadence DOUBLE,
    max_cadence DOUBLE,

    avg_power_w DOUBLE,
    max_power_w DOUBLE,

    calories INTEGER,

    avg_temperature_c DOUBLE,
    max_temperature_c DOUBLE,

    swim_stroke VARCHAR,
    total_strokes INTEGER,
    avg_swolf DOUBLE
);

CREATE TABLE IF NOT EXISTS intervals (
    interval_id BIGINT PRIMARY KEY,

    activity_id VARCHAR NOT NULL,

    parent_interval_id BIGINT,

    sequence_number INTEGER,

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,

    duration_seconds DOUBLE,

    interval_type VARCHAR,
    source VARCHAR,

    event VARCHAR,
    event_type VARCHAR,
    lap_trigger VARCHAR,

    target_type VARCHAR,
    target_value DOUBLE,
    target_value_high DOUBLE,
    target_unit VARCHAR,

    distance_m DOUBLE,

    avg_heart_rate INTEGER,
    min_heart_rate INTEGER,
    max_heart_rate INTEGER,

    avg_speed_m_s DOUBLE,
    max_speed_m_s DOUBLE,

    avg_cadence DOUBLE,
    max_cadence DOUBLE,

    avg_power_w DOUBLE,
    max_power_w DOUBLE,

    ascent_m DOUBLE,
    descent_m DOUBLE
);

CREATE TABLE IF NOT EXISTS developer_fields (
    developer_field_id BIGINT PRIMARY KEY,

    activity_id VARCHAR NOT NULL,

    timestamp TIMESTAMP,

    message_type VARCHAR NOT NULL,

    developer_data_index INTEGER,

    field_definition_number INTEGER,

    field_name VARCHAR NOT NULL,

    unit VARCHAR,

    value_numeric DOUBLE,
    value_text VARCHAR
);

CREATE TABLE IF NOT EXISTS lengths (
    length_id BIGINT PRIMARY KEY,

    activity_id VARCHAR NOT NULL,

    timestamp TIMESTAMP,
    start_time TIMESTAMP,

    duration_seconds DOUBLE,
    elapsed_seconds DOUBLE,

    length_type VARCHAR,

    distance_m DOUBLE,

    avg_speed_m_s DOUBLE,
    avg_cadence DOUBLE,

    swim_stroke VARCHAR,

    total_strokes INTEGER,

    calories INTEGER,

    avg_swolf DOUBLE
);

CREATE TABLE IF NOT EXISTS events (
    event_id BIGINT PRIMARY KEY,

    activity_id VARCHAR NOT NULL,

    timestamp TIMESTAMP NOT NULL,

    event VARCHAR,
    event_type VARCHAR,
    timer_trigger VARCHAR
);