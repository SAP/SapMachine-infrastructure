'''
Copyright (c) 2021-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import sys
import utils

from os.path import join
from zipfile import ZipFile

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--major', help='The SapMachine major version to build', metavar='MAJOR')
    parser.add_argument('-d', '--dir', help='The dir to extract jtreg to', metavar='DIR')
    args = parser.parse_args()

    version_input = []
    if 'SAPMACHINE_VERSION' in os.environ:
        version_input.append(os.environ['SAPMACHINE_VERSION'])
    if 'GIT_REF' in os.environ:
        version_input.append(os.environ['GIT_REF'])
    major = utils.calc_major(filter(None, version_input)) if args.major is None else int(args.major)
    if major is None:
        return -1

    if major > 19:
        url = 'https://github.com/SAP/SapMachine-infrastructure/releases/download/jtreg-7.1.1/jtreg.zip'
    else:
        url = 'https://github.com/SAP/SapMachine-infrastructure/releases/download/jtreg-6.1/jtreg.zip'

    dir = os.getcwd() if args.dir is None else args.dir

    print(str.format('Downloading "{0}" and extracting to "{1}"', url, dir ))

    archive_path = join(dir, 'jtreg.zip')
    utils.remove_if_exists(archive_path)
    utils.download_artifact(url, archive_path)
    path = join(dir, 'jtreg')
    utils.remove_if_exists(path)
    os.makedirs(path)
    with ZipFile(archive_path, 'r') as zipObj:
      zipObj.extractall(path)

    utils.remove_if_exists(archive_path)

    return 0

if __name__ == "__main__":
    sys.exit(main())
