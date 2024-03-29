'''
Copyright (c) 2018-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import re
import requests
import sys
import utils

from os.path import join
from versions import SapMachineTag

def download_cf_yaml(url):
    cf_18_lines = []
    response = requests.get(url)
    lines = response.text.splitlines()
    for line in lines:
        if line.startswith("1.8."):
            cf_18_lines.append(line)
    return cf_18_lines

def write_index_yaml(assets, cf_18_lines, target):
    if not os.path.exists(target):
        os.makedirs(target) 
    with open(join(target, "index.yml"), "w+") as index_yaml:
        index_yaml.write("---\n")
        for line in cf_18_lines:
            index_yaml.write(str.format("{0}\n", line))
        for version in sorted(assets):
            index_yaml.write(str.format("{0}: {1}\n", version, assets[version]))

def main(argv=None):
    releases = utils.github_api_request('releases', per_page=300)
    if releases is None:
        print("Could not get releases from GitHub")
        sys.exit(-1)

    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    asset_map_jdk, asset_map_jre = {}, {}
    for release in releases:
        if release['prerelease'] is True:
            continue

        t = SapMachineTag.from_string(release['name'])
        if t is None:
            continue

        assets = release['assets']
        for asset in assets:
            match = asset_pattern.match(asset['name'])
            if match is None:
                continue

            asset_image_type = match.group(1)
            asset_os = match.group(3)

            if asset_os == 'linux-x64':
                sapmachine_version = t.get_version()
                build_number = t.get_build_number()

                buildpack_version = str.format('{0}.{1}.{2}_{3}.{4}.b{5}',
                    sapmachine_version[0],
                    sapmachine_version[1],
                    sapmachine_version[2],
                    sapmachine_version[3],
                    sapmachine_version[4],
                    build_number if build_number else '0')

                if asset_image_type == 'jre':
                    asset_map_jre[buildpack_version] = asset['browser_download_url']
                else:
                    asset_map_jdk[buildpack_version] = asset['browser_download_url']

    local_repo = join(os.getcwd(), 'gh-pages')
    utils.git_clone('github.com/SAP/SapMachine.git', 'gh-pages', local_repo)
    
    # Since SapMachine has no release 8, we add the OpenJDK 8 versions from CF to our index.yml
    cf_bionic18_lines = download_cf_yaml("https://java-buildpack.cloudfoundry.org/openjdk/bionic/x86_64/index.yml")
    write_index_yaml(asset_map_jre, cf_bionic18_lines, join(local_repo, 'assets', 'cf', 'jre', 'linux', 'x86_64'))
    write_index_yaml(asset_map_jdk, cf_bionic18_lines, join(local_repo, 'assets', 'cf', 'jdk', 'linux', 'x86_64'))
    write_index_yaml(asset_map_jre, cf_bionic18_lines, join(local_repo, 'assets', 'cf', 'jre', 'bionic', 'x86_64'))
    write_index_yaml(asset_map_jdk, cf_bionic18_lines, join(local_repo, 'assets', 'cf', 'jdk', 'bionic', 'x86_64'))
    
    # Since SapMachine has no release 8, we add the OpenJDK 8 versions from CF to our index.yml
    cf_jammy18_lines = download_cf_yaml("https://java-buildpack.cloudfoundry.org/openjdk/jammy/x86_64/index.yml")
    write_index_yaml(asset_map_jre, cf_jammy18_lines, join(local_repo, 'assets', 'cf', 'jre', 'jammy', 'x86_64'))
    write_index_yaml(asset_map_jdk, cf_jammy18_lines, join(local_repo, 'assets', 'cf', 'jdk', 'jammy', 'x86_64'))

    utils.git_commit(local_repo, 'Update version list for Cloud Foundry buildpacks', ['assets'])
    utils.git_push(local_repo)
    utils.remove_if_exists(local_repo)

    return 0

if __name__ == "__main__":
    sys.exit(main())
