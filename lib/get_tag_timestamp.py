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

from os.path import join

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine Git tag', metavar='TAG', required=True)
    args = parser.parse_args()

    releases = utils.github_api_request('releases', per_page=100)

    if releases is not None:
        for release in releases:
            if release['tag_name'] == args.tag:
                print(release['published_at'].split('T')[0])

if __name__ == "__main__":
    sys.exit(main())