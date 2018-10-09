#!/usr/bin/env python
import click
import subprocess
from os import path, makedirs


DS_VERSION = '2018.04.18'
S3_HTTP_PREFIX = 'https://s3-us-west-2.amazonaws.com/pinafore-us-west-2/qanta-jmlr-datasets/'
S3_AWS_PREFIX = 's3://pinafore-us-west-2/qanta-jmlr-datasets/'
LOCAL_QANTA_PREFIX = 'data/'

QANTA_UNMAPPED_DATASET_PATH = f'qanta.unmapped.{DS_VERSION}.json'
QANTA_PROCESSED_DATASET_PATH = f'qanta.processed.{DS_VERSION}.json'
QANTA_FOLDED_DATASET_PATH = f'qanta.folded.{DS_VERSION}.json'
QANTA_MAPPED_DATASET_PATH = f'qanta.mapped.{DS_VERSION}.json'
QANTA_SQLITE_DATASET_PATH = f'qanta.{DS_VERSION}.sqlite3'
QANTA_TRAIN_DATASET_PATH = f'qanta.train.{DS_VERSION}.json'
QANTA_DEV_DATASET_PATH = f'qanta.dev.{DS_VERSION}.json'
QANTA_TEST_DATASET_PATH = f'qanta.test.{DS_VERSION}.json'

FILES = [
    QANTA_UNMAPPED_DATASET_PATH,
    QANTA_PROCESSED_DATASET_PATH,
    QANTA_FOLDED_DATASET_PATH,
    QANTA_MAPPED_DATASET_PATH,
    QANTA_SQLITE_DATASET_PATH,
    QANTA_TRAIN_DATASET_PATH,
    QANTA_DEV_DATASET_PATH,
    QANTA_TEST_DATASET_PATH
]

DATASET_CHOICES = {
    'qanta_full': FILES,
}


def make_file_pairs(file_list, source_prefix, target_prefix):
    return [(path.join(source_prefix, f), path.join(target_prefix, f)) for f in file_list]


def shell(command):
    return subprocess.run(command, check=True, shell=True, stderr=subprocess.STDOUT)


def download_file(http_location, local_location):
    print(f'Downloading {http_location} to {local_location}')
    makedirs(path.dirname(local_location), exist_ok=True)
    shell(f'wget -O {local_location} {http_location}')


@click.group()
def main():
    """
    CLI utility for managing any datasets related to qanta
    """
    pass


@main.command()
@click.option('--local-qanta-prefix', default=LOCAL_QANTA_PREFIX)
@click.option('--local-plotting-prefix', default=LOCAL_PLOTTING_PREFIX)
@click.option('--dataset', default='qanta_minimal',
              type=click.Choice(['qanta_full']))
def download(local_qanta_prefix, local_plotting_prefix, dataset):
    """
    Download the qanta dataset
    """
    if dataset == 'qanta_minimal' or dataset == 'qanta_full':
        for s3_file, local_file in make_file_pairs(DATASET_CHOICES[dataset], S3_HTTP_PREFIX, local_qanta_prefix):
            download_file(s3_file, local_file)
    elif dataset == 'wikidata':
        download_file(WIKIDATA_S3, WIKIDATA_PATH)
    elif dataset == 'plotting':
        print('Downloading datasets used for generating plots: squad, triviaqa, simplequestions, jeopardy')
        for s3_file, local_file in make_file_pairs(DATASET_FILES, S3_HTTP_PREFIX, local_plotting_prefix):
            download_file(s3_file, local_file)
    else:
        raise ValueError('Unrecognized dataset')


@main.command()
def upload():
    """
    Upload the qanta dataset to S3. This requires write permissions on s3://pinafore-us-west-2
    """
    for local_file, s3_file in make_file_pairs(FILES + TORCH_FILES, LOCAL_QANTA_PREFIX, S3_AWS_PREFIX):
        print(f'Uploading {local_file} to {s3_file}')
        shell(f'aws s3 cp {local_file} {s3_file}')


if __name__ == '__main__':
    main()
