import glob
import os
import shutil
import zipfile

import boto3
from botocore import client, UNSIGNED
from tqdm.contrib.concurrent import process_map

BUCKET_NAME = 'hubway-data'
DATA_DIR = 'data'

boto_config = client.Config(
    region_name='us-east-2',
    signature_version=UNSIGNED,  # anonymous public access credentials
    retries={
        'max_attempts': 3,
        'mode': 'standard'
    }
)
s3 = boto3.client('s3', config=boto_config)


def download_and_extract(workers):
    s3_files = _get_files_to_download(BUCKET_NAME)
    print("==== Downloading files from S3 ====")
    process_map(_download_file, s3_files, max_workers=workers)
    zip_files = _get_files_to_unzip()
    print("==== Unzipping files ====")
    process_map(_extract_zip, zip_files, max_workers=workers)

    # some of the BB files were zipped with hidden __MACOSX directories
    mac_artifact = os.path.join(DATA_DIR, '__MACOSX')
    shutil.rmtree(mac_artifact)


def _download_file(object_to_download):
    object_name, size = object_to_download
    file_name = object_name.split('/')[-1]
    file_path = os.path.join(DATA_DIR, file_name)

    if os.path.isfile(file_path) and os.stat(file_path).st_size == size:
        return
    else:
        s3.download_file(BUCKET_NAME, object_name, file_path)


def _get_files_to_download(bucket):
    response = s3.list_objects_v2(Bucket=bucket)
    files_in_bucket = [(item['Key'], item['Size']) for item in response['Contents']]
    return files_in_bucket


def _get_files_to_unzip():
    pattern = os.path.join(DATA_DIR, '*.zip')
    return glob.glob(pattern)


def _extract_zip(zip_file):
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(DATA_DIR)
