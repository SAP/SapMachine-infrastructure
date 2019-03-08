'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import re
import utils
import yaml

from urllib2 import urlopen, Request, quote, HTTPError

cf_yml_url = 'https://sap.github.io/SapMachine/assets/cf/jre/linux/x86_64/index.yml'
cf_version_pattern = re.compile('(((\d+)\.(\d+)\.(\d+))\.(\d+)\.(\d+))_b(\d+)')

def main(argv=None):
    request = Request(cf_yml_url)
    versions_found = 0

    try:
        response = urlopen(request)
    except HTTPError, e:
        return 1

    try:
        runtimes = yaml.safe_load(response)

        for version in runtimes:
            versions_found += 1
            match = cf_version_pattern.match(version)

            if match is None:
                return 1

            url = runtimes[version]
            print(str.format('found version "{0}" with url "{1}"', version, url))
            request = Request(url)

            try:
                response = urlopen(request)
                if response.code != 200:
                    return 1

            except HTTPError, e:
                return 1

    except yaml.YAMLError as e:
        return 1

    if versions_found == 0:
        print('no versions found in buildpack data ...')
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())