'''
Copyright (c) 2001-2021 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

from argparse import ArgumentParser
import sys
import utils
import os
from os.path import join
from zipfile import ZipFile

def main(argv=None):
    parser = ArgumentParser()
    parser.add_argument('-m', '--major', help='the SapMachine major version to build', metavar='MAJOR', required=True)
    parser.add_argument('-d', '--dir', help='The dir to extract jtreg to', metavar='DIR', required=True)
    args = parser.parse_args()

    ver = int(args.major)
    if ver >= 17:
        url = 'https://github.com/SAP/SapMachine-infrastructure/releases/download/jtreg-6/jtreg.zip'
        name = 'jtreg.zip'
    else:
        url = 'https://github.com/SAP/SapMachine-infrastructure/releases/download/jtreg-5.1/jtreg.zip'
        name = 'jtreg.zip'

    print(str.format('Downloading "{0}" and extracting to "{1}"', url, args.dir ))

    archive_path = join(args.dir, name)
    utils.remove_if_exists(archive_path)
    utils.download_artifact(url, archive_path)
    path = join(args.dir, 'jtreg')
    utils.remove_if_exists(path)
    os.makedirs(path)
    with ZipFile(archive_path, 'r') as zipObj:
      zipObj.extractall(path)

    utils.remove_if_exists(archive_path)

if __name__ == "__main__":
    sys.exit(main())
