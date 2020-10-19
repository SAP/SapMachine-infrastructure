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
openjdk_git_base = 'https://github.com/'

jdk_major_start = 11

exception_list = [
    'jdk/jdk11',
    'jdk/jdk12',
    'jdk-updates/jdk12u',
    'jdk-updates/jdk12u-dev',
    'jdk/jdk13',
    'jdk-updates/jdk13u',
    'jdk-updates/jdk13u-dev',
    'jdk/jdk14',
    'jdk-updates/jdk14u',
    'jdk-updates/jdk14u-dev',
    'jdk/jdk15',
    'jdk/jdk'
]

def test_repositories(scm_base, repository_base, repository_suffix = ''):
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
        request = Request(scm_base + repository)

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
    parser.add_argument('-m', '--mercurial', help='enumerate mercurial repositories, instead of git', action='store_true', default=False)
    args = parser.parse_args()

    openjdk_repositories = []

    if args.mercurial:
        openjdk_repositories.extend(test_repositories(openjdk_hg_base, 'jdk/jdk'))
        openjdk_repositories.extend(test_repositories(openjdk_hg_base, 'jdk-updates/jdk', 'u'))
        openjdk_repositories.extend(test_repositories(openjdk_hg_base, 'jdk-updates/jdk', 'u-dev'))
    else:
        openjdk_repositories.append('openjdk/jdk')
        #openjdk_repositories.extend(test_repositories(openjdk_git_base, 'openjdk/jdk'))

    print(args.separator.join(openjdk_repositories))
    return 0

if __name__ == "__main__":
    sys.exit(main())
