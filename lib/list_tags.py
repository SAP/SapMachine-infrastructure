'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import sys

from utils import github_api_request
from versions import SapMachineTag

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

    releases = github_api_request('releases', per_page=300)

    for release in releases:
        if release['prerelease'] is True and not include_prereleases:
            continue

        tag = SapMachineTag.from_string(release['name'])

        if tag is None:
            continue

        major = tag.get_major()

        if major is None or str(major) != requested_major:
            continue

        tag_list.append(release['name'])

    print(separator.join([tag for tag in tag_list]))

    return 0

if __name__ == "__main__":
    sys.exit(main())
