import os
import sqlite3
import glob
import shutil

from src.sql import table_drop, table_create
from src.download import DATA_DIR, download_and_extract
from src.insert import (evenly_distribute_csv_files_for_insert_by_total_size,
                        print_csv_header,
                        DATABASE,
                        insert_rows_from_list_of_csvs)

from tqdm.contrib.concurrent import process_map

if __name__ == '__main__':
    worker_count = os.cpu_count()

    # create the temporary directory for storing the zip files and CSVs
    os.mkdir(DATA_DIR)
    download_and_extract(worker_count)

    # pattern = os.path.join(DATA_DIR, '*tripdata.csv')
    # files = [(file, os.path.getsize(file)) for file in glob.glob(pattern)]
    # for file, size in files:
    #     print_csv_header(file)
    #
    print("==== Recreating database ====")
    # drop and recreate the table in the db file before inserting the records
    db = sqlite3.connect(DATABASE, isolation_level=None)
    db.execute(table_drop)
    db.execute(table_create)
    db.close()

    print("==== Inserting with %s workers ====" % worker_count)
    distribution = evenly_distribute_csv_files_for_insert_by_total_size(
        worker_count)
    process_map(insert_rows_from_list_of_csvs, distribution.items(),
                max_workers=worker_count)

    # clean up all downloaded data to reduce the size of the docker image
    #shutil.rmtree(DATA_DIR)
