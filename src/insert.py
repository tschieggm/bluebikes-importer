import os
import sqlite3
import csv
import glob

import re

from src import sql
from src.download import DATA_DIR
from datetime import datetime

from tqdm.contrib.concurrent import process_map

# extracts YYYYMM from file names
MONTH_YEAR_RE = r'(20[0-4]\d)(0[1-9]|1[0-2])'
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATABASE = 'bluebike.sqlite'


def distribute_csv_files_to_insert(num_workers):
    # find all CSV files and their sizes
    pattern = os.path.join(DATA_DIR, '*tripdata.csv')
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


def insert_rows_from_list_of_csvs(args):
    worker, files = args
    id_gap = worker * 100000000
    memory_conn = sqlite3.connect(':memory:', timeout=10, isolation_level=None)
    _configure_sqlite_pragma(memory_conn, "memory")
    cursor = memory_conn.cursor()
    cursor.execute(sql.table_create)
    cursor.execute(sql.id_insert, [id_gap])

    for f in files:
        _insert_rows_from_single_csv(f, memory_conn, cursor)

    cursor.execute("delete from bluebikes where rowid=?", [id_gap])

    file_conn = sqlite3.connect(DATABASE, isolation_level=None)
    _configure_sqlite_pragma(file_conn)

    # Insert data from the in-memory table to the file-based table
    memory_conn.execute('ATTACH DATABASE "%s" AS filedb' % DATABASE)
    memory_conn.execute('INSERT INTO filedb.bluebikes SELECT * FROM bluebikes')
    memory_conn.execute('DETACH DATABASE filedb')
    memory_conn.close()
    file_conn.close()


def print_csv_header(file):
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            print((file, row))
            return


def _insert_rows_from_single_csv(file, conn, cursor):
    year, month = re.findall(MONTH_YEAR_RE, file)[0]
    month_year = int('%s%s' % (year, month))
    # Each process creates its own database connection

    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        bulk_insert_size = 1000
        insert_count = 0
        passed_header_row = False
        data_to_insert = []
        for row in reader:
            if not passed_header_row:
                passed_header_row = True
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

            if insert_count == bulk_insert_size:
                _bulk_insert_by_schema(data_to_insert, month_year, cursor, conn)
                insert_count = 0
                data_to_insert = []

    # insert any outstanding records from the latch batch
    _bulk_insert_by_schema(data_to_insert, month_year, cursor, conn)


def _bulk_insert_by_schema(data_to_insert, month_year, cursor, connection):
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


def _configure_sqlite_pragma(connection, journal_mode="WAL"):
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA journal_mode = %s" % journal_mode)
    connection.execute('PRAGMA busy_timeout = 30000')