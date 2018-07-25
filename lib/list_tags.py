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

from urllib2 import urlopen, Request, quote
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

    token = utils.get_github_api_accesstoken()
    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases', org, repository)
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())
    for release in response:
        if release['prerelease'] is True and not include_prereleases:
            continue

        version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])

        if major is None or major != requested_major or os_ext:
            continue

        tag_list.append(release['name'])

    print(separator.join([tag for tag in tag_list]))

if __name__ == "__main__":
    sys.exit(main())
