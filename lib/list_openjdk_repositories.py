'''
Copyright (c) 2019-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import sys

from urllib.error import HTTPError
from urllib.request import urlopen, Request

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
    'openjdk/jdk11',
    'openjdk/jdk12',
    'openjdk/jdk12u',
    'openjdk/jdk12u-dev',
    'openjdk/jdk13',
    'openjdk/jdk13u',
    'openjdk/jdk13u-dev',
    'openjdk/jdk14',
    'openjdk/jdk14u',
    'openjdk/jdk14u-dev',
    'openjdk/jdk15',
    'openjdk/jdk15u',
    'openjdk/jdk15u-dev',
    'openjdk/jdk16',
    'openjdk/jdk16u',
    'openjdk/jdk16u-dev',
    'openjdk/jdk17',
    'openjdk/jdk18',
    'openjdk/jdk18u',
    'openjdk/jdk19'
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
    args = parser.parse_args()

    openjdk_repositories = []

    openjdk_repositories.append('openjdk/jdk')
    openjdk_repositories.extend(test_repositories(openjdk_git_base, 'openjdk/jdk'))
    openjdk_repositories.extend(test_repositories(openjdk_git_base, 'openjdk/jdk', 'u'))
    openjdk_repositories.extend(test_repositories(openjdk_git_base, 'openjdk/jdk', 'u-dev'))

    print(args.separator.join(openjdk_repositories))

    return 0

if __name__ == "__main__":
    sys.exit(main())
