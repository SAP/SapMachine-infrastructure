'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils
import argparse

from utils import github_api_request
from os.path import join

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--major', help='the SapMachine major version', metavar='MAJOR', required=True)
    parser.add_argument('-s', '--separator', help='the separator char', metavar='SEPARATOR', required=False, default=' ')
    parser.add_argument('-p', '--include-prereleases', help='include pre-releases', action='store_true', default=False)
    args = parser.parse_args()

    requested_major = args.major
    separator = args.separator
    include_prereleases = args.include_prereleases
    tag_list = []

    releases = github_api_request('releases')

    for release in releases:
        if release['prerelease'] is True and not include_prereleases:
            continue

        version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])

        if major is None or major != requested_major or os_ext:
            continue

        tag_list.append(release['name'])

    print(separator.join([tag for tag in tag_list]))

if __name__ == "__main__":
    sys.exit(main())
