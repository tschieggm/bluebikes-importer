import glob
import os
import shutil
import zipfile

import boto3
from botocore import client, UNSIGNED
from tqdm.contrib.concurrent import process_map

BUCKET_NAME = 'hubway-data'

boto_config = client.Config(
    region_name='us-east-2',
    signature_version=UNSIGNED,  # anonymous public access credentials
    retries={
        'max_attempts': 3,
        'mode': 'standard'
    }
)
s3 = boto3.client('s3', config=boto_config)


def download_and_extract(workers, data_dir):
    s3_files = _get_files_to_download(BUCKET_NAME)
    print("==== Downloading files from S3 ====")
    target_dirs = [data_dir] * len(s3_files)
    process_map(_download_file, s3_files, target_dirs, max_workers=workers)
    zip_files = _get_files_to_unzip(data_dir)
    print("==== Unzipping files ====")
    process_map(_extract_zip, zip_files, target_dirs, max_workers=workers)

    # some of the BB files were zipped with hidden __MACOSX directories
    mac_artifact = os.path.join(data_dir, '__MACOSX')
    shutil.rmtree(mac_artifact)


def _download_file(object_to_download, data_dir):
    object_name, size = object_to_download
    file_name = object_name.split('/')[-1]
    file_path = os.path.join(data_dir, file_name)
    if os.path.isfile(file_path) and os.stat(file_path).st_size == size:
        return
    else:
        s3.download_file(BUCKET_NAME, object_name, file_path)


def _get_files_to_download(bucket):
    response = s3.list_objects_v2(Bucket=bucket)
    files_in_bucket = [(item['Key'], item['Size']) for item in response['Contents']]
    return files_in_bucket


def _get_files_to_unzip(data_dir):
    pattern = os.path.join(data_dir, '*.zip')
    return glob.glob(pattern)


def _extract_zip(zip_file, data_dir):
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(data_dir)
