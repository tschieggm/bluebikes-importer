import os
import sqlite3
import shutil

from src import sql
from src import insert
from src import download

from tqdm.contrib.concurrent import process_map


if __name__ == '__main__':
    worker_count = os.cpu_count()

    # create the temporary directory for storing the zip files and CSVs
    os.mkdir(download.DATA_DIR)
    download.download_and_extract(worker_count)

    print("==== Recreating database ====")
    # drop and recreate the table in the db file before inserting the records
    db = sqlite3.connect(insert.DATABASE, isolation_level=None)
    db.execute(sql.table_drop)
    db.execute(sql.table_create)
    db.close()

    print("==== Inserting with %s workers ====" % worker_count)
    distribution = insert.evenly_distribute_csv_files_for_insert_by_total_size(worker_count)
    process_map(insert.insert_rows_from_list_of_csvs, distribution.items(), max_workers=worker_count)

    # clean up all downloaded data to reduce the size of the docker image
    shutil.rmtree(download.DATA_DIR)
