import json
import os
import pprint

import pandas as pd
import argparse
from tqdm import tqdm
from haversine import haversine, Unit

# 25 meters seems to be the sweet spot to minimize false positives and negatives
DEFAULT_MAX_DISTANCE_METERS = 25

# hard coded station mappings that tend to subvert the automated process.
# This is usually due to proximity to other different stations.
MANUAL_MAPPINGS = {
    # Congress St at Boston City Hall. Conflicts with Gov center
    '44': 'D32009',

    # The following stations are from test data or mobile stations
    '438': 'BCU-ARCHIVE',
    '223': 'BCU-ARCHIVE',
    '382': 'BCU-ARCHIVE',
    '229': 'BCU-ARCHIVE',
    '383': 'BCU-ARCHIVE',
    '230': 'BCU-ARCHIVE',
    '158': 'BCU-ARCHIVE',
    '164': 'BCU-ARCHIVE',
}


# simple encoder to json.dumps data with sets
class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


# Function to search for the file in the specified directories
def find_csv_file(directories, filename):
    for directory in directories:
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            return file_path
    return None


# Look for the specified csv file in a few directories to try loading it
def load_input_csv(filename):
    directories_to_check = [
        ".",
        "data",
        os.path.join('src', 'tools', 'legacy_station_mapping'),
        os.path.join('tests', 'test_files', 'legacy_station_mapping'),
    ]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    step_up_to_root = os.path.join('..', '..', '..')
    project_dir = os.path.abspath(os.path.join(script_dir, step_up_to_root))
    absolute_directories = [os.path.join(project_dir, dir) for dir in
                            directories_to_check]
    csv_file_path = find_csv_file(absolute_directories, filename)

    if csv_file_path:
        print(f"Found CSV file at: {csv_file_path}")
        df = pd.read_csv(str(csv_file_path))
        print("CSV file loaded successfully.")
        return df
    else:
        raise FileNotFoundError("CSV file not found.")


# calculate the distance between two coordinates in km
def calculate_distance(lat1, lng1, lat2, lng2):
    return haversine((lat1, lng1), (lat2, lng2), unit=Unit.METERS)


# print out stations with duplicate mappings (123|45 -> ABC001)
def log_duplicates(station_id_mapping):
    duplicates = {}
    for key, values in station_id_mapping.items():
        for value in values:
            if value not in duplicates:
                duplicates[value] = set()
            duplicates[value].add(key)

    duplicate_mappings = {key: values for key, values in duplicates.items() if
                          len(values) > 1}
    if duplicate_mappings:
        print("\nDuplicate mappings %d:" % len(duplicate_mappings))
        for key, value in duplicate_mappings.items():
            print(f'{key}: {value}')
    else:
        print("No duplicate mappings found.")


# print out stations with multiple mappings (123 -> ABC001|ABC002)
def log_multiples(station_id_mapping):
    multiples = {}
    for key, values in station_id_mapping.items():
        if len(values) > 1:
            multiples[key] = values
    if len(multiples.items()) > 0:
        print("\nMultiple mappings %d:" % len(multiples))
        for key, value in multiples.items():
            print(f'{key}: {value}')
    else:
        print("\nNo multiple mappings found.")


# print out stations that couldn't be inferred
def log_missing(missing_mappings):
    print("\nMissing Mappings %d:" % len(missing_mappings))
    pprint.pp(missing_mappings)


def format_results(station_id_mapping, missing_station_id_mapping):
    known_mapping = {}
    for key, values in station_id_mapping.items():
        if len(values) > 1:
            raise RuntimeError("Multiple mappings found. Please resolve.")
        if len(values) == 0:
            continue
        known_mapping[key] = values.pop()

    sorted_known_mappings = dict(
        sorted(known_mapping.items(), key=lambda i: int(i[0])))
    results = {
        'known_mappings': sorted_known_mappings,
        'missing_mappings': missing_station_id_mapping
    }

    return results


def generate_mapping(filename, max_distance=DEFAULT_MAX_DISTANCE_METERS,
                     verbose=False, write_to_disk=False):
    df = load_input_csv(filename)
    print("Matching stations under %d meters" % max_distance)

    station_id_mapping = {}
    missing_mappings = {}
    ride_count = 0

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
        ride_count += int(row['count'])
        closest_id = None
        closest_distance = float('inf')

        if start_id not in station_id_mapping:
            station_id_mapping[start_id] = set()

        if start_id in MANUAL_MAPPINGS.keys():
            station_id_mapping[start_id].add(MANUAL_MAPPINGS[start_id])
            continue

        for other_index, other_row in df.iterrows():
            if other_row['start_id'] in df_filtered['start_id'].values:
                # Ignore rows that are legacy ids
                continue
            if index == other_index:
                # skip self record
                continue

            other_id = other_row['start_id']
            other_lat = other_row['start_lat']
            other_lng = other_row['start_lng']
            other_station_name = other_row['start_station_name']

            # Short circuit if station names match directly
            if start_station_name.lower() == other_station_name.lower():
                station_id_mapping[start_id].add(other_id)
                closest_distance = float('inf')
                break

            # Calculate distance using haversine
            distance = calculate_distance(start_lat, start_lng, other_lat,
                                          other_lng)
            if distance < closest_distance:
                closest_id = other_id
                closest_distance = distance

        # Add the closest match to the id_mapping if it is within max distance
        if closest_distance <= max_distance:
            station_id_mapping[start_id].add(closest_id)

        if len(station_id_mapping[start_id]) == 0:
            if start_id in missing_mappings:
                missing_mappings[start_id].add(start_station_name)
            else:
                missing_mappings[start_id] = {start_station_name}

    if verbose:
        log_duplicates(station_id_mapping)
        log_multiples(station_id_mapping)
        log_missing(missing_mappings)

    results = format_results(station_id_mapping, missing_mappings)
    print("\nReconciled %d worth of rides" % ride_count)
    print("\nMapped %d stations" % len(results['known_mappings']))

    if write_to_disk:
        json.dump(results, open("results.json", 'w'), cls=SetEncoder)
    else:
        return results


def main_cli():
    parser = argparse.ArgumentParser(description="""
        Tool to generate a mapping of legacy ids to new ids based on station
        names and coordinates based on an input query described in the README.md
    """)
    parser.add_argument('-filename',
                        default="station_mapping_input.csv",
                        help="""
        Input CSV containing station facets from ride data
    """)
    parser.add_argument('-meters', '--max-distance-meters',
                        default=DEFAULT_MAX_DISTANCE_METERS,
                        help="""
        The maximum radius in km to qualify a station as a match.
        Lower numbers produce fewer false positives.
        The default should be suitable for most cases.
    """)
    parser.add_argument("--write-to-disk", action="store_true",
                        help="Writes the results to disk")
    parser.add_argument("--verbose", action="store_true",
                        help="Increases the verbosity for more detailed logging")
    args = parser.parse_args()
    generate_mapping(args.filename, int(args.max_distance_meters),
                     args.verbose, args.write_to_disk)


if __name__ == '__main__':
    main_cli()
