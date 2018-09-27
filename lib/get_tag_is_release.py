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
    parser.add_argument('-t', '--tag', help='the SapMachine Git tag', metavar='TAG', required=True)
    args = parser.parse_args()

    token = utils.get_github_api_accesstoken()
    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases', org, repository)

    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())

    for release in response:
        if release['tag_name'] == args.tag:
            print(str(not release['prerelease']).lower())

if __name__ == "__main__":
    sys.exit(main())