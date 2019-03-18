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

def write_index_yaml(assets, target):
    with open(join(target, 'index.yml'), 'w+') as index_yaml:
        index_yaml.write('---\n')
        for version in sorted(assets):
            index_yaml.write(str.format('{0}: {1}\n', version, assets[version]))

def main(argv=None):
    token = utils.get_github_api_accesstoken()
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    asset_map = {}

    releases = utils.github_api_request('releases', per_page=100)

    for release in releases:
        if release['prerelease'] is True:
            continue

        version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])
        assets = release['assets']

        if version is None or os_ext:
            continue

        for asset in assets:
            match = asset_pattern.match(asset['name'])

            if match is not None:
                asset_image_type = match.group(1)
                asset_os = match.group(3)

                if asset_os == 'linux-x64' and asset_image_type == 'jre':
                    sapmachine_version = [int(e) for e in version_part.split('.')]
                    sapmachine_version += [0 for sapmachine_version in range(0, 5 - len(sapmachine_version))]

                    if sap_build_number:
                        sapmachine_version[4] = int(sap_build_number)

                    buildpack_version = str.format('{0}.{1}.{2}_{3}.{4}.b{5}',
                        sapmachine_version[0],
                        sapmachine_version[1],
                        sapmachine_version[2],
                        sapmachine_version[3],
                        sapmachine_version[4],
                        build_number if build_number else '0')
                    asset_map[buildpack_version] = asset['browser_download_url']

    local_repo = join(os.getcwd(), 'gh-pages')
    utils.git_clone('github.com/SAP/SapMachine.git', 'gh-pages', local_repo)
    write_index_yaml(asset_map, join(local_repo, 'assets', 'cf', 'jre', 'linux', 'x86_64'))
    utils.git_commit(local_repo, 'Updated index.yml', ['assets'])
    utils.git_push(local_repo)
    utils.remove_if_exists(local_repo)

if __name__ == "__main__":
    sys.exit(main())
