'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils

from urllib2 import urlopen, Request, quote
from os.path import join
from string import Template

#'linux-x64-musl': 'Linux x64 musl',
os_description = {
    'linux-x64':             { 'ordinal': 1, 'name': 'Linux x64' },
    'linux-ppc64le':         { 'ordinal': 2, 'name': 'Linux ppc64le' },
    'linux-ppc64':           { 'ordinal': 3, 'name': 'Linux ppc64' },
    'windows-x64':           { 'ordinal': 4, 'name': 'Windows x64'},
    'windows-x64-installer': { 'ordinal': 5, 'name': 'Windows x64 Installer'},
    'osx-x64':               { 'ordinal': 6, 'name': 'macOS x64'}
}

image_type_description = {
    'jdk':  { 'ordinal': 1, 'name': 'JDK' },
    'jre':  { 'ordinal': 2, 'name': 'JRE' },
}

latest_template = '''---
layout: default
title: Latest SapMachine ${major} Release
redirect_to:
  - ${url}
---
'''

class Releases:
    def __init__(self, major):
        self.major = major
        self.releases = {}

    def add_asset(self, asset_url, image_type, os, tag):
        if tag not in self.releases:
            self.releases[tag] = {}

        if image_type not in self.releases[tag]:
            self.releases[tag][image_type] = {}

        self.releases[tag][image_type][os] = asset_url

    def clear_assets(self):
        self.releases.clear()

    def transform(self):
        json_root = {
            self.major: {
                'releases': []
            }
        }

        for tag in sorted(self.releases, reverse=True):
            release = {
                'tag': tag
            }

            for image_type in self.releases[tag]:
                release[image_type] = {}
                for os in self.releases[tag][image_type]:
                    release[image_type][os] = self.releases[tag][image_type][os]

            json_root[self.major]['releases'].append(release)

        return json_root

def push_to_git(files):
    local_repo = join(os.getcwd(), 'gh-pages')
    utils.git_clone('github.com/SAP/SapMachine.git', 'gh-pages', local_repo)

    for _file in files:
        location = join(local_repo, _file['location'])
        if not os.path.exists(os.path.dirname(location)):
            os.makedirs(os.path.dirname(location))
        with open(location, 'w+') as out:
            out.write(_file['data'])
        utils.git_commit(local_repo, _file['commit_message'], [location])

    utils.git_push(local_repo)
    utils.remove_if_exists(local_repo)

def main(argv=None):
    token = utils.get_github_api_accesstoken()
    org = 'SAP'
    repository = 'SapMachine'
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    major_dict = {}
    release_dict = {}
    image_dict = {}
    latest_link_dict = {}

    releases = utils.github_api_request('releases', per_page=100)

    for release in releases:
        version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])

        is_prerelease = release['prerelease']

        if version is None or os_ext:
            continue

        if major in major_dict:
            if not is_prerelease and major_dict[major]:
                # this is not a pre-release but the release before this was a pre-release
                # remove all assets
                if major in release_dict:
                    release_dict[major].clear_assets()

                # remove entry in the image dictionary
                if major in image_dict:
                    del image_dict[major]
            else:
                if not major_dict[major]:
                    # the release before this was a release
                    # skip, we only keep the latest release version
                    continue

        major_dict[major] = is_prerelease
        assets = release['assets']

        if is_prerelease is not True and major not in latest_link_dict:
            latest_link_dict[major] = Template(latest_template).substitute(
                major=major,
                url = release['html_url']
            )

        has_dmg = False

        for asset in assets:
            match = asset_pattern.match(asset['name'])

            if match is not None:
                asset_image_type = match.group(1)
                asset_os = match.group(3)
                file_type = match.group(4)

                if asset_os == 'windows-x64' and file_type == '.msi':
                    asset_os = 'windows-x64-installer'

                if asset_os == 'osx-x64':
                    if file_type == '.dmg':
                        has_dmg = True
                    elif has_dmg:
                        continue

                tag = release['name']
                image_is_lts = utils.sapmachine_is_lts(major) and not release['prerelease']

                if major not in image_dict:
                    image_dict[major] = {
                        'label': str.format('SapMachine {0}', major),
                        'lts': image_is_lts,
                        'ea': release['prerelease']
                    }

                if major in release_dict:
                    releases_for_major = release_dict[major]
                else:
                    releases_for_major = Releases(major)
                    release_dict[major] = releases_for_major

                release_dict[major].add_asset(asset['browser_download_url'], asset_image_type, asset_os, tag)

    latest_lts_version = 0
    latest_non_lts_version = 0

    for major in image_dict:
        if image_dict[major]['lts'] and int(major) > latest_lts_version:
            latest_lts_version = int(major)
        if not image_dict[major]['lts'] and not image_dict[major]['ea'] and int(major) > latest_non_lts_version:
            latest_non_lts_version = int(major)

    json_root = {
        'majors':[],
        'imageTypes':[],
        'os':[],
        'assets':{}
    }

    for major in sorted(image_dict):
        add = False
        if image_dict[major]['lts']:
            if int(major) >= latest_lts_version:
                add = True
        else:
            if int(major) >= latest_non_lts_version and int(major) >= latest_lts_version:
                add = True

        if add:
            json_root['majors'].append({'id': major, 'label': image_dict[major]['label'], 'lts': image_dict[major]['lts'], 'ea': image_dict[major]['ea']})
        else:
            del image_dict[major]

    def get_os_key(os):
        return os_description[os]['ordinal']

    def get_image_type_key(image_type):
        return image_type_description[image_type]['ordinal']

    for os in sorted(os_description, key=get_os_key):
        json_root['os'].append({'key': os, 'value': os_description[os]['name'], 'ordinal': os_description[os]['ordinal']})

    for image_type in sorted(image_type_description, key=get_image_type_key):
        json_root['imageTypes'].append({'key': image_type, 'value': image_type_description[image_type]['name'], 'ordinal': image_type_description[image_type]['ordinal']})

    for major in release_dict:
        if major in image_dict:
            json_root['assets'].update(release_dict[major].transform())

    files = [
        {
            'location': join('assets', 'data', 'sapmachine_releases.json'),
            'data': json.dumps(json_root, indent=4),
            'commit_message': 'Updated release data.'
        }
    ]

    for major in latest_link_dict:
        files.append({
            'location': join('latest', major, 'index.md'),
            'data': latest_link_dict[major],
            'commit_message': str.format('Updated latest link for SapMachine {0}', major)
        })

    push_to_git(files)

    #with open('website_data.json', 'w') as website_data_json:
    #    website_data_json.write(json.dumps(json_root, indent=4))

    return 0

if __name__ == "__main__":
    sys.exit(main())
