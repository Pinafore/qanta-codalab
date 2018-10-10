import click
import subprocess
from os import path, makedirs


DS_VERSION = '2018.04.18'
S3_HTTP_PREFIX = 'https://s3-us-west-2.amazonaws.com/pinafore-us-west-2/qanta-jmlr-datasets/'
QANTA_MAPPED_DATASET_PATH = f'qanta.mapped.{DS_VERSION}.json'
QANTA_TRAIN_DATASET_PATH = f'qanta.train.{DS_VERSION}.json'
QANTA_DEV_DATASET_PATH = f'qanta.dev.{DS_VERSION}.json'
QANTA_TEST_DATASET_PATH = f'qanta.test.{DS_VERSION}.json'

FILES = [
    QANTA_MAPPED_DATASET_PATH,
    QANTA_TRAIN_DATASET_PATH,
    QANTA_DEV_DATASET_PATH,
    QANTA_TEST_DATASET_PATH
]


def make_file_pairs(file_list, source_prefix, target_prefix):
    return [(path.join(source_prefix, f), path.join(target_prefix, f)) for f in file_list]


def shell(command):
    return subprocess.run(command, check=True, shell=True, stderr=subprocess.STDOUT)


def download_file(http_location, local_location):
    print(f'Downloading {http_location} to {local_location}')
    makedirs(path.dirname(local_location), exist_ok=True)
    shell(f'wget -O {local_location} {http_location}')


def download(local_qanta_prefix):
    """
    Download the qanta dataset
    """
    for s3_file, local_file in make_file_pairs(FILES, S3_HTTP_PREFIX, local_qanta_prefix):
        download_file(s3_file, local_file)
