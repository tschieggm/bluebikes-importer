table_drop = "DROP TABLE IF EXISTS bluebikes; "

table_create = """
CREATE TABLE bluebikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    src_file TEXT NOT NULL,
    trip_duration INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    start_id INTEGER NOT NULL,
    start_station_name TEXT NOT NULL,
    start_lat REAL NOT NULL,
    start_lng REAL NOT NULL,
    end_id INTEGER NOT NULL,
    end_station_name TEXT NOT NULL,
    end_lat REAL NOT NULL,
    end_lng REAL NOT NULL,
    ride_id INTEGER NOT NULL,
    usertype TEXT NOT NULL,
    birth_year INTEGER,
    gender TEXT,    
    rideable_type TEXT,
    postal_code TEXT
);
"""

# all records up to and including 202004-bluebikes-tripdata.csv
insert_stmt = """
INSERT INTO bluebikes (  
    src_file,          
    trip_duration,
    started_at, 
    ended_at,
    start_id,
    start_station_name,
    start_lat,
    start_lng,
    end_id,
    end_station_name,
    end_lat,
    end_lng,
    ride_id,
    usertype,
    birth_year,
    gender,
    postal_code
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

# id insert
id_insert = """
INSERT INTO bluebikes (  
    id,
    src_file,          
    trip_duration,
    started_at, 
    ended_at,
    start_id,
    start_station_name,
    start_lat,
    start_lng,
    end_id,
    end_station_name,
    end_lat,
    end_lng,
    ride_id,
    usertype
)
VALUES (?, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1);
"""