'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils
import argparse
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import HTTPError

openjdk_hg_base = 'http://hg.openjdk.java.net/'
jdk_major_start = 11
exception_list = [
    'jdk/jdk11',
    'jdk/jdk12',
    'jdk-updates/jdk12u',
    'jdk-updates/jdk12u-dev',
    'jdk/jdk13',
    'jdk-updates/jdk13u',
    'jdk-updates/jdk13u-dev'
]

def test_repositories(repository_base, repository_suffix=''):
    openjdk_repositories = []
    code = 200
    jdk_major = jdk_major_start
    retries = 10

    while code == 200 or retries > 0:
        repository = repository_base + str(jdk_major) + repository_suffix
        jdk_major += 1

        if repository in exception_list:
            continue

        retries -= 1
        request = Request(openjdk_hg_base + repository)

        try:
            response = urlopen(request)
            code = response.code
            openjdk_repositories.append(repository)
        except HTTPError as e:
            code = e.code

    return openjdk_repositories

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--separator', help='the separator char', metavar='SEPARATOR', required=False, default=' ')
    args = parser.parse_args()

    openjdk_repositories = ['jdk/jdk']

    openjdk_repositories.extend(test_repositories('jdk/jdk'))
    openjdk_repositories.extend(test_repositories('jdk-updates/jdk', 'u'))
    openjdk_repositories.extend(test_repositories('jdk-updates/jdk', 'u-dev'))

    print(args.separator.join(openjdk_repositories))
    return 0

if __name__ == "__main__":
    sys.exit(main())