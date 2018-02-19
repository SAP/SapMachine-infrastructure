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

def write_index_yaml(assets, target):
    with open(join(target, 'index.yml'), 'w+') as index_yaml:
        index_yaml.write('---\n')
        for version in sorted(assets):
            index_yaml.write(str.format('{0}: {1}\n', version, assets[version]))

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--major', help='the SapMachine major version', metavar='MAJOR', required=True)
    args = parser.parse_args()

    token = utils.get_github_api_accesstoken()
    github_api = 'https://api.github.com/repos/SAP/SapMachine/releases'
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    asset_map = {}

    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())
    for release in response:
        if release['prerelease'] is True:
            continue

        version, version_part, major, build_number, sap_build_number = utils.sapmachine_tag_components(release['name'])
        assets = release['assets']

        if args.major == major:
            for asset in assets:
                match = asset_pattern.match(asset['name'])

                if match is not None:
                    asset_image_type = match.group(1)
                    asset_os = match.group(3)

                    if asset_os == 'linux-x64' and asset_image_type == 'jre':
                        buildpack_version = ''
                        parts = version_part.split('.')
                        num_parts = len(parts)
                        if num_parts == 3:
                            buildpack_version = str.format('{0}_', version_part)
                        elif num_parts < 3:
                            buildpack_version = str.format('{0}{1}_', version_part, '.0' * (3 - num_parts))
                        elif num_parts > 3:
                            buildpack_version = str.format('{0}.{1}.{2}_{3}', parts[0], parts[1], parts[2], parts[3])

                        buildpack_version += str.format('b{0}', build_number)

                        if sap_build_number:
                            buildpack_version += str.format('s{0}', sap_build_number)

                        asset_map[buildpack_version] = asset['browser_download_url']

    local_repo = join(os.getcwd(), 'gh-pages')
    utils.git_clone('github.com/SAP/SapMachine.git', 'gh-pages', local_repo)
    write_index_yaml(asset_map, join(local_repo, 'assets', 'cf', 'jre', args.major, 'linux', 'x86_64'))
    utils.git_commit(local_repo, 'Updated index.yml', ['assets'])
    utils.git_push(local_repo)
    utils.remove_if_exists(local_repo)

if __name__ == "__main__":
    sys.exit(main())
