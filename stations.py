import csv
import os
from collections import defaultdict

from src.models.ride import BluebikeRide
from src.models.station import BluebikeStation

STATION_FILE_v1 = "Hubway_Stations_2011_2016.csv"
STATION_FILE_v2 = "previous_Hubway_Stations_as_of_July_2017.csv"
STATION_FILE_v3 = "Hubway_Stations_as_of_July_2017.csv"

TEST_RIDE_FILE = "202009-bluebikes-tripdata.csv"

station_mappings = defaultdict(int)
repeat_offenders = defaultdict(int)


def read_stations():
    stations = []
    file_v1 = os.path.join("data", STATION_FILE_v1)
    file_v2 = os.path.join("data", STATION_FILE_v2)
    file_v3 = os.path.join("data", STATION_FILE_v3)

    for file in [file_v1, file_v2, file_v3]:
        with open(file, newline='') as csvfile:
            header_map = BluebikeStation.headers_by_file_name(csvfile.name)
            reader = csv.DictReader(csvfile, fieldnames=header_map, delimiter=',',
                                    quotechar='"')
            next(reader)  # skip the header row
            for row in reader:
                station = BluebikeStation.from_csv_row_dict(file, row)
                stations.append(station)

    return stations


def calculate_distances(reference_point, stations):
    distances = []
    for station in stations:
        distance = station.distance_from_point(reference_point)
        distances.append(distance)
    return sorted(distances)[0:5]


def match_station_by_name(ride, stations):
    for station in stations:
        if station.name == ride.start_station_name:
            # check the distance
            if station.distance_from_point(ride.start_point) > 500:  # meters
                raise AssertionError("Station should be within 500 meters")
            else:
                return station
    return None


def associate_stations(ride, station):
    if (station.identity, ride.start_id) in station_mappings:
        station_mappings[(station.identity, ride.start_id)] += 1
    else:
        station_mappings[(station.identity, ride.start_id)] = 1


def find_closest_station(ride, stations, min_threshold=75, next_distance=50):
    matching_station_by_name = match_station_by_name(ride, stations)
    if matching_station_by_name:
        return matching_station_by_name, 0

    distances = [(s, s.distance_from_point(ride.start_point)) for s in stations]
    distances.sort(key=lambda x: x[1])  # sort stations by distance

    # Check if the closest station is within 5 meters and no other stations
    # within 50 meters
    closest_distance = distances[0][1]
    next_closest_distance = distances[1][1]
    if closest_distance < min_threshold and (
            next_closest_distance - closest_distance) > next_distance:
        return distances[0]
    elif ride.start_station_name == distances[0][0].name:
        return distances[0]

    nearest_stations = distances[0:5]
    # If no specific close station is found, return the three closest
    print("==================================")
    print(ride)
    for station, distance in nearest_stations:
        print(f"File: {station.file_name} Station: {station.name}, Distance: {distance} meters")
    x = nearest_stations[0][0].identity
    mapping_count = repeat_offenders[x, ride.start_id]
    print(f'{x}, {ride.start_id}: {mapping_count}')
    repeat_offenders[(x, ride.start_id)] += 1
    raise ValueError("Failed to find matching station")


def foo():
    stations = read_stations()
    file = os.path.join("data", TEST_RIDE_FILE)
    header_map = BluebikeRide.headers_by_file_name(TEST_RIDE_FILE)
    matched = 0
    unmatched = 0

    with open(file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=header_map, delimiter=',',
                                quotechar='"')
        next(reader)  # skip the header row
        for row in reader:
            if unmatched >= 400:
                break
            ride = BluebikeRide.from_csv_row_dict(TEST_RIDE_FILE, row)

            try:
                closest_station, distance = find_closest_station(ride, stations)
                associate_stations(ride, closest_station)
                # print(closest_station)
                matched += 1
            except ValueError:
                # print(row)
                unmatched += 1
                continue

    print(f"Matched {matched} stations")
    print(f"Unmatched {unmatched} stations")
    print(repeat_offenders)


def compare_stations():
    stations_map = {}

    file_v1 = os.path.join("data", STATION_FILE_v1)
    file_v2 = os.path.join("data", STATION_FILE_v2)
    file_v3 = os.path.join("data", STATION_FILE_v3)

    for file in [file_v1, file_v2, file_v3]:
        stations_map[file] = []
        with open(file, newline='') as csvfile:
            header_map = BluebikeStation.headers_by_file_name(csvfile.name)
            reader = csv.DictReader(csvfile, fieldnames=header_map, delimiter=',',
                                    quotechar='"')
            next(reader)  # skip the header row
            for row in reader:
                station = BluebikeStation.from_csv_row_dict(file, row)
                stations_map[file].append(station)
        stations_map[file].sort(key=lambda x: x.identity)

    return stations_map


if __name__ == '__main__':
    #foo()
    stations_map = compare_stations()

    pass
