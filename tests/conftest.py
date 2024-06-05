import os
import pytest
import sqlite3


@pytest.fixture(scope="session")
def fixture_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_files")

@pytest.fixture(scope="session")
def csv_dir(fixture_dir):
    return os.path.join(fixture_dir, "csvs")



@pytest.fixture(scope="function")
def empty_in_mem_database_connection():
    with sqlite3.connect(":memory") as conn:
        cursor = conn.cursor()
        yield cursor
