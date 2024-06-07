import json

import pandas as pd
import argparse
from tqdm import tqdm
from haversine import haversine


# Define the maximum distance (in kilometers) for matching
MAX_DISTANCE_KM = 0.030


# Create a function to check if two coordinates are within the
# specified distance
def within_distance(lat1, lng1, lat2, lng2, max_distance_km):
    return haversine((lat1, lng1), (lat2, lng2)) <= max_distance_km


def generate_mapping(filename):
    df = pd.read_csv(filename)
    print("Successfully loaded csv file: %s" % filename)

    # Create an empty dictionary to store the ID mappings
    id_mapping = {}

    missing_mappings = set()

    # Filter the dataframe to ensure the left side of the mapping has an
    # integer ID less than 1000
    df['start_id_int'] = pd.to_numeric(df['start_id'], errors='coerce')
    df_filtered = df[df['start_id_int'].notnull() & (df['start_id_int'] < 1000)]

    # Iterate through the filtered dataframe and create the ID mapping
    for index, row in tqdm(df_filtered.iterrows(), total=df_filtered.shape[0],
                           desc="Processing Rows"):
        start_id = row['start_id']
        start_lat = row['start_lat']
        start_lng = row['start_lng']
        start_station_name = row['start_station_name']

        id_mapping[start_id] = []

        for other_index, other_row in df.iterrows():
            # Ignore rows that are in df_filtered
            if other_row['start_id'] in df_filtered['start_id'].values:
                continue

            if index != other_index:
                other_id = other_row['start_id']
                other_lat = other_row['start_lat']
                other_lng = other_row['start_lng']
                other_station_name = other_row['start_station_name']

                # Short circuit if station names match directly
                if start_station_name.lower() == other_station_name.lower():
                    id_mapping[start_id].append(other_id)
                    continue

                if within_distance(start_lat, start_lng, other_lat, other_lng,
                                   MAX_DISTANCE_KM):
                    id_mapping[start_id].append(other_id)

        if len(id_mapping[start_id]) == 0:
            id_mapping[start_id].append(start_station_name)
            missing_mappings.add(start_id)

    # Check for duplicate mappings
    duplicates = {}
    for key, values in id_mapping.items():
        for value in values:
            if value not in duplicates:
                duplicates[value] = []
            duplicates[value].append(key)

    duplicate_mappings = {key: values for key, values in duplicates.items() if
                          len(values) > 1}

    # Print duplicate mappings if any
    if duplicate_mappings:
        print("Duplicate Mappings %s:" % len(duplicate_mappings))
        for key, value in duplicate_mappings.items():
            print(f'{key}: {value}')
    else:
        print("No duplicate mappings found.")

    print("Missing Mappings %s:" % len(missing_mappings))
    print(missing_mappings)

    # Print the ID mapping
    sorted_mapping = dict(sorted(id_mapping.items(), key=lambda i: int(i[0])))
    json.dump(sorted_mapping, open("results.json", 'w'))


def main_cli():
    parser = argparse.ArgumentParser(description="""
        Tool to generate a mapping  of legacy ids to new ids based on station
        names and GPS coordinates based on the query below:
        
        select
          start_id,
          start_station_name,
          start_lat,
          start_lng,
          count(0)
        from
          bluebikes
        where
          (rideable_type != 'electric_bike' or rideable_type is NULL)
        group by
          1,
          2,
          3,
          4
        order by
          start_station_name
          
        Note that this is an n^2 operation that can take some time.
    """)
    parser.add_argument('filename', help="""
        Input CSV containing station facets from ride data
    """)

    args = parser.parse_args()
    generate_mapping(args.filename)


if __name__ == '__main__':
    main_cli()
