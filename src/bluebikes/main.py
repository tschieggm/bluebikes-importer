import argparse
import os
import sqlite3
import shutil

from bluebikes import sql
from bluebikes import insert
from bluebikes import download

from tqdm.contrib.concurrent import process_map

def main_cli():
    parser = argparse.ArgumentParser(description="Download Blue Bikes data as CSV files, then load them into a SQLite Database called bluebike.sqlite")
    parser.add_argument("-d", "--data_dir", default="data", 
                    help="A folder to store Blue Bikes CSV files downloaded from the S3 bucket. Defaults to 'data'."
                    )
    parser.add_argument("--no_cleanup", action="store_true", 
                    help="By default, the folder where CSV files will be deleted at the end."\
                          "Use this flag if you don't want to deleted them. This is useful for debugging purposes.")
    args = parser.parse_args()
    main(args.data_dir, not args.no_cleanup)


def main(data_dir, is_cleanup_downloads=True):
    worker_count = os.cpu_count()

    # create the temporary directory for storing the zip files and CSVs
    os.makedirs(data_dir, exist_ok=True)
    download.download_and_extract(worker_count, data_dir)

    print("==== Recreating database ====")
    # drop and recreate the table in the db file before inserting the records
    db = sqlite3.connect(insert.DATABASE, isolation_level=None)
    db.execute(sql.table_drop)
    db.execute(sql.table_create)
    db.close()

    print("==== Inserting with %s workers ====" % worker_count)
    distribution = insert.evenly_distribute_csv_files_for_insert_by_total_size(worker_count, data_dir)
    process_map(insert.insert_rows_from_list_of_csvs, distribution.items(), [insert.DATABASE] * len(distribution) , max_workers=worker_count)

    # clean up all downloaded data to reduce the size of the docker image
    if is_cleanup_downloads:
        shutil.rmtree(data_dir)


if __name__ == '__main__':
    main_cli()