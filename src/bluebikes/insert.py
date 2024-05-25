import csv
import glob
import os
import re
import sqlite3
from datetime import datetime

from bluebikes import sql

# extracts YYYYMM from file names
MONTH_YEAR_RE = r'(20[0-4]\d)(0[1-9]|1[0-2])'
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATABASE = 'bluebike.sqlite'
BULK_INSERT_SIZE = 1000
DATABASE_LOCK_TIMEOUT = 300  # 5 minutes


def evenly_distribute_csv_files_for_insert_by_total_size(num_workers, data_dir):
    # find all CSV files and their sizes
    pattern = os.path.join(data_dir, '*tripdata.csv')
    files = [(file, os.path.getsize(file)) for file in glob.glob(pattern)]

    # sort files by size in descending order (optional but helps in distribution)
    files.sort(key=lambda x: x[1], reverse=True)

    # initialize distribution dictionary
    distribution = {i: [] for i in range(num_workers)}  # Each worker has an empty list of files
    workers = [{'id': i, 'total_size': 0} for i in range(num_workers)]

    # distribute files uniformly across workers
    for file, size in files:
        # Find the worker with the minimum total size
        min_worker = min(workers, key=lambda x: x['total_size'])
        distribution[min_worker['id']].append(file)  # Add only file path, not size
        min_worker['total_size'] += size

    return distribution


def insert_rows_from_list_of_csvs(worker_assignments, database=DATABASE):
    worker_number, files = worker_assignments
    memory_conn, cursor = _initialize_in_memory_database(worker_number)

    for f in files:
        _insert_rows_from_single_csv(f, cursor)

    _dump_memory_db_to_file(memory_conn, database)
    memory_conn.close()


def print_csv_header(file):
    """
    Helper function to print the first line of a CSV file. Useful for schema debugging
    """
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            print((file, row))
            return


def _insert_rows_from_single_csv(file, cursor):
    year, month = re.findall(MONTH_YEAR_RE, file)[0]
    month_year = int('%s%s' % (year, month))

    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        insert_count = 0
        passed_header_row = False
        data_to_insert = []
        for row in reader:
            if not passed_header_row:
                passed_header_row = True
                # ensure we skip the header row
                continue

            row.insert(0, file)
            data_to_insert.append(row)
            insert_count += 1

            # newer records drop duration
            if 202304 <= month_year:
                end_date = datetime.strptime(row[4], DATE_FORMAT)
                start_date = datetime.strptime(row[3], DATE_FORMAT)
                time_delta = end_date - start_date
                row.insert(3, time_delta.total_seconds())

            if insert_count == BULK_INSERT_SIZE:
                _bulk_insert_by_schema(data_to_insert, month_year, cursor)
                insert_count = 0
                data_to_insert = []

    # insert any outstanding records from the latch batch
    _bulk_insert_by_schema(data_to_insert, month_year, cursor)


def _bulk_insert_by_schema(data_to_insert, month_year, cursor):
    if month_year <= 202004:
        insert_stmt = sql.insert_stmt_v0
    elif 202005 <= month_year <= 202303:
        insert_stmt = sql.insert_stmt_v1
    elif 202304 <= month_year:
        insert_stmt = sql.insert_stmt_v2
    else:
        return
    try:
        cursor.executemany(insert_stmt, data_to_insert)
    except Exception as e:
        print(e)
        # print(data_to_insert)


def _initialize_in_memory_database(worker_number):
    memory_conn = sqlite3.connect(':memory:', timeout=DATABASE_LOCK_TIMEOUT, isolation_level=None)
    _configure_sqlite_pragma(memory_conn, "memory")
    cursor = memory_conn.cursor()
    cursor.execute(sql.table_create)
    _seed_auto_increment(cursor, worker_number)

    return memory_conn, cursor


def _configure_sqlite_pragma(connection, journal_mode="WAL"):
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA journal_mode = %s" % journal_mode)
    connection.execute('PRAGMA busy_timeout = %s' % (DATABASE_LOCK_TIMEOUT * 1000))


def _seed_auto_increment(cursor, worker_number):
    """
    This insert will seed the auto-increment primary key at a value related to the worker number.
    This is required to avoid ID collisions when dumping the in-memory database into the file.
    It will be deleted immediately.
    """
    auto_increment_start_id = worker_number * 100000000
    cursor.execute(sql.id_insert, [auto_increment_start_id])
    cursor.execute("delete from bluebikes where rowid=?", [auto_increment_start_id])


def _dump_memory_db_to_file(memory_conn, database=DATABASE):
    """
    Insert data from the in-memory table to the file-based table
    """
    file_conn = sqlite3.connect(database, timeout=DATABASE_LOCK_TIMEOUT, isolation_level=None)
    _configure_sqlite_pragma(file_conn)
    memory_conn.execute('ATTACH DATABASE "%s" AS filedb' % database)
    memory_conn.execute('INSERT INTO filedb.bluebikes SELECT * FROM bluebikes')
    memory_conn.execute('DETACH DATABASE filedb')
    file_conn.close()
