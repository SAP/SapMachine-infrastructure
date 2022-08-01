'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import re
import sys
import yaml
from urllib.request import urlopen, Request
from urllib.error import HTTPError

cf_yml_url = 'https://sap.github.io/SapMachine/assets/cf/jre/linux/x86_64/index.yml'
cf_version_pattern = re.compile('(\d+)\.(\d+)\.(\d+)_(\d+)(\.(\d+))?(\.b(\d+))?')

def main(argv=None):
    request = Request(cf_yml_url)
    versions_found = 0

    try:
        response = urlopen(request)
    except HTTPError as e:
        print(str.format('Error loading {0}', cf_yml_url))
        return 1

    try:
        runtimes = yaml.safe_load(response)

        for version in runtimes:
            versions_found += 1
            match = cf_version_pattern.match(version)

            if match is None:
                print(str.format('Error: No match for {0}', version))
                return 1

            url = runtimes[version]
            print(str.format('Found version "{0}" with url "{1}"', version, url))
            request = Request(url)

            try:
                response = urlopen(request)
                if response.code != 200:
                    print(str.format('Error ({0}) opening {1}', response.code, url))
                    return 1

            except HTTPError as e:
                print(str.format('HTTPError opening {0}: {1}', url, e))
                return 1

    except yaml.YAMLError as e:
        print(str.format('YAMLError: {0}', e))
        return 1

    if versions_found == 0:
        print('Error: No versions found in buildpack data')
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
