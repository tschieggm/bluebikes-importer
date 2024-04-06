import os
import sqlite3
import shutil

from src import sql
from src import insert
from src import download

from tqdm.contrib.concurrent import process_map


if __name__ == '__main__':
    workers = os.cpu_count()
    download.download_and_extract(workers)

    print("==== Recreating database ====")
    # drop and recreate the table in the db file before inserting the records
    db = sqlite3.connect(insert.DATABASE, isolation_level=None)
    db.execute(sql.table_drop)
    db.execute(sql.table_create)
    db.close()

    print("==== Inserting with %s workers ====" % workers)
    distribution = insert.distribute_csv_files_to_insert(workers)
    process_map(insert.insert_rows_from_list_of_csvs, distribution.items(), max_workers=workers)

    # clean up all downloaded data to reduce the size of the docker image
    shutil.rmtree(download.DATA_DIR)
