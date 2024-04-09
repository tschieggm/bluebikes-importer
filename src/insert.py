import csv
import glob
import os
import sqlite3

from src import sql
from src.download import DATA_DIR
from src.models.ride import BluebikeRide

DATABASE = 'bluebike.sqlite'
BULK_INSERT_SIZE = 1000
DATABASE_LOCK_TIMEOUT = 300  # 5 minutes


def evenly_distribute_csv_files_for_insert_by_total_size(num_workers):
    # find all CSV files and their sizes
    pattern = os.path.join(DATA_DIR, '*tripdata.csv')
    files = [(file, os.path.getsize(file)) for file in glob.glob(pattern)]

    # sort files by size in descending order
    files.sort(key=lambda x: x[1], reverse=True)

    # initialize distribution dictionary
    distribution = {i: [] for i in range(num_workers)}
    workers = [{'id': i, 'total_size': 0} for i in range(num_workers)]

    # distribute files uniformly across workers
    for file, size in files:
        # Find the worker with the minimum total size
        min_worker = min(workers, key=lambda x: x['total_size'])
        distribution[min_worker['id']].append(file)
        min_worker['total_size'] += size

    return distribution


def insert_rows_from_list_of_csvs(args):
    worker_number, files = args
    memory_conn, cursor = _initialize_in_memory_database(worker_number)

    for f in files:
        _insert_rows_from_single_csv(f, cursor)

    _dump_memory_db_to_file(memory_conn)
    memory_conn.close()


def print_csv_header(file):
    """
    Helper function to print the first line of a CSV file. Useful for schema debugging
    """
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        year_month = BluebikeRide.parse_file_year_month(file)
        print((year_month, next(reader)))
        return


def _insert_rows_from_single_csv(file_name, cursor):
    with open(file_name, newline='') as csvfile:
        header_map = BluebikeRide.headers_by_file_name(file_name)
        reader = csv.DictReader(csvfile, fieldnames=header_map, delimiter=',',
                                quotechar='"')
        next(reader)  # skip the header row
        insert_count = 0
        data_to_insert = []

        for row in reader:
            ride = BluebikeRide.from_csv_row_dict(file_name, row)
            data_to_insert.append(ride.to_row_for_insert())
            insert_count += 1

            if insert_count == BULK_INSERT_SIZE:
                _bulk_insert_by_schema(data_to_insert, cursor)
                insert_count = 0
                data_to_insert = []

    # insert any outstanding records from the latch batch
    _bulk_insert_by_schema(data_to_insert, cursor)


def _bulk_insert_by_schema(data_to_insert, cursor):
    insert_stmt = sql.insert_stmt
    cursor.executemany(insert_stmt, data_to_insert)


def _initialize_in_memory_database(worker_number):
    memory_conn = sqlite3.connect(':memory:', timeout=DATABASE_LOCK_TIMEOUT,
                                  isolation_level=None)
    _configure_sqlite_pragma(memory_conn, "memory")
    cursor = memory_conn.cursor()
    cursor.execute(sql.table_create)
    _seed_auto_increment(cursor, worker_number)

    return memory_conn, cursor


def _configure_sqlite_pragma(connection, journal_mode="WAL"):
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA journal_mode = %s" % journal_mode)
    connection.execute(
        'PRAGMA busy_timeout = %s' % (DATABASE_LOCK_TIMEOUT * 1000))


def _seed_auto_increment(cursor, worker_number):
    """
    This insert will seed the auto-increment primary key at a value related to the worker number.
    This is required to avoid ID collisions when dumping the in-memory database into the file.
    It will be deleted immediately.
    """
    auto_increment_start_id = worker_number * 100000000
    cursor.execute(sql.id_insert, [auto_increment_start_id])
    cursor.execute("delete from bluebikes where rowid=?",
                   [auto_increment_start_id])


def _dump_memory_db_to_file(memory_conn):
    """
    Insert data from the in-memory table to the file-based table
    """
    file_conn = sqlite3.connect(DATABASE, timeout=DATABASE_LOCK_TIMEOUT,
                                isolation_level=None)
    _configure_sqlite_pragma(file_conn)
    memory_conn.execute('ATTACH DATABASE "%s" AS filedb' % DATABASE)
    memory_conn.execute('INSERT INTO filedb.bluebikes SELECT * FROM bluebikes')
    memory_conn.execute('DETACH DATABASE filedb')
    file_conn.close()
