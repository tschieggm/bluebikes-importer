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
# There is also a section here dedicated to test stations not used by the public
MANUAL_MAPPINGS = {
    # Congress St at Boston City Hall. Conflicts with Gov center
    '44': 'D32009',

    # Labeled as 'TD Garden - Causeway at Portal Park #1' but has coordinates incorrectly matched with its relocation.
    # Its must closer in location to the Portal Park #2 station (D32003). Park #1 ends up at West End Park
    '109': 'D32003',

    # Boylston St at Dartmouth St. Conflicts with legacy New Balance station
    '134': 'D32055',

    # Hard coded station for 'Clarendon St at Commonwealth Ave' which also captures a poorly named legacy station
    # "Copley Square - Dartmouth St at Boylston St" that had incorrect coordinates
    '36': 'BCU-384-36',
    '384': 'BCU-384-36',

    # Strange name that deviates from its peers
    '498': 'Broadway Opposite Norwood Ave  (Temp Winter Station)',

    # The following stations are from test data or mobile stations
    '153': 'BCU-ARCHIVE',
    '158': 'BCU-ARCHIVE',
    '164': 'BCU-ARCHIVE',
    '223': 'BCU-ARCHIVE',
    '229': 'BCU-ARCHIVE',
    '230': 'BCU-ARCHIVE',
    '382': 'BCU-ARCHIVE',
    '383': 'BCU-ARCHIVE',
    '438': 'BCU-ARCHIVE',

    # Standalone legacy stations far enough from others that justify their own identifier
    '534': 'Adams Branch Library',
    '450': 'Beacon St at Englewood Ave',
    '453': 'Beacon St at Hawes St',
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
        os.path.join('data', 'processed'),
        os.path.join('src', 'bluebikes', 'stations'),
        os.path.join('tests', 'test_files', 'legacy_stations'),
    ]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    step_up_to_root = os.path.join('..', '..', '..', '..')
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
        raise FileNotFoundError(
            "CSV file not found in %s." % absolute_directories)


# calculate the distance between two coordinates in km
def calculate_distance(lat1, lng1, lat2, lng2):
    return haversine((lat1, lng1), (lat2, lng2), unit=Unit.METERS)


# There are ~1k records with a GPS coordinate pointing to the wrong place with the wrong ID and name.
# I have no idea if the coordinates or the ID is wrong, so I assumed the coordinates where based on a
# temporary winter station that exited here.
def is_bad_hospital(start_lat, start_lng, start_station_name):
    if start_station_name != "Somerville Hospital":
        return False
    bad_station_coordinates = (42.396775418355034, -71.10237520492547)
    distance_meters = calculate_distance(start_lat, start_lng, *bad_station_coordinates)
    if distance_meters > DEFAULT_MAX_DISTANCE_METERS:
        return False
    return True


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
        if len(values) > 1 and 'BCU-BAD-HOSPITAL' in values:
            # this station is wonk but shouldn't raise a multiple mappings error
            print("Found a bad hospital.")
        if len(values) > 1 and key != '156':  # this station is wonk
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

    # Filter the dataframe to ensure the left side of the mapping has an
    # integer ID less than 1000
    df['station_id_int'] = pd.to_numeric(df['station_id'], errors='coerce')
    df_filtered = df[df['station_id_int'].notnull() & (df['station_id_int'] < 1000)]

    # Iterate through the filtered dataframe and create the ID mapping
    for index, row in tqdm(df_filtered.iterrows(), total=df_filtered.shape[0],
                           desc="Processing Rows"):
        station_id = row['station_id']
        lat = row['lat']
        lng = row['lng']
        station_name = row['station_name']
        closest_id = None
        closest_distance = float('inf')

        if station_id not in station_id_mapping:
            station_id_mapping[station_id] = set()

        if station_id in MANUAL_MAPPINGS.keys():
            station_id_mapping[station_id].add(MANUAL_MAPPINGS[station_id])
            continue
        if is_bad_hospital(lat, lng, station_name):
            station_id_mapping[station_id].add('BCU-BAD-HOSPITAL')
            continue

        for other_index, other_row in df.iterrows():
            if other_row['station_id'] in df_filtered['station_id'].values:
                # Ignore rows that are legacy ids
                continue
            if index == other_index:
                # skip self record
                continue

            other_id = other_row['station_id']
            other_lat = other_row['lat']
            other_lng = other_row['lng']
            other_station_name = other_row['station_name']

            # Short circuit if station names match directly
            if station_name.lower() == other_station_name.lower():
                station_id_mapping[station_id].add(other_id)
                closest_distance = float('inf')
                break

            # Calculate distance using haversine
            distance = calculate_distance(lat, lng, other_lat,
                                          other_lng)
            if distance < closest_distance:
                closest_id = other_id
                closest_distance = distance

        # Add the closest match to the id_mapping if it is within max distance
        if closest_distance <= max_distance:
            station_id_mapping[station_id].add(closest_id)

        if len(station_id_mapping[station_id]) == 0:
            if station_id in missing_mappings:
                missing_mappings[station_id].add(station_name)
            else:
                missing_mappings[station_id] = {station_name}

    if verbose:
        log_duplicates(station_id_mapping)
        log_multiples(station_id_mapping)
        log_missing(missing_mappings)

    results = format_results(station_id_mapping, missing_mappings)
    print("\nMapped %d stations" % len(results['known_mappings']))

    if write_to_disk:
        json.dump(results, open("../results.json", 'w'), cls=SetEncoder)
    else:
        return results


def main_cli():
    parser = argparse.ArgumentParser(description="""
        Tool to generate a mapping of legacy ids to new ids based on station
        names and coordinates based on an input query described in the README.md
    """)
    parser.add_argument('-filename',
                        default="legacy_station_input.csv",
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
