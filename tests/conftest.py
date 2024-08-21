import os
import pytest
import sqlite3


@pytest.fixture(scope="session")
def fixture_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_files")


@pytest.fixture(scope="session")
def csv_dir(fixture_dir):
    return os.path.join(fixture_dir, "csvs")


@pytest.fixture(scope="session")
def legacy_stations_dir(fixture_dir):
    return os.path.join(fixture_dir, "legacy_stations")


@pytest.fixture(scope="session")
def published_stations_dir(fixture_dir):
    return os.path.join(fixture_dir, "published_stations")


@pytest.fixture(scope="session")
def remedial_stations_input_file(fixture_dir):
    return os.path.join(fixture_dir, "remedial_stations", "station_input.csv")


@pytest.fixture(scope="function")
def empty_in_mem_database_connection():
    with sqlite3.connect(":memory") as conn:
        cursor = conn.cursor()
        yield cursor
