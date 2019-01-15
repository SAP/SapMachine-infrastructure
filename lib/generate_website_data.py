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
    'linux-x64':     { 'ordinal': 1, 'name': 'Linux x64' },
    'linux-ppc64le': { 'ordinal': 2, 'name': 'Linux ppc64le' },
    'linux-ppc64':   { 'ordinal': 3, 'name': 'Linux ppc64' },
    'windows-x64':   { 'ordinal': 4, 'name': 'Windows x64'},
    'osx-x64':       { 'ordinal': 5, 'name': 'macOS x64'}
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

    def add_asset(self, asset_url, os, tag):
        if tag not in self.releases:
            self.releases[tag] = {}

        self.releases[tag][os] = asset_url

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

            for os in self.releases[tag]:
                release[os] = self.releases[tag][os]

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

def is_lts(major):
    return int(major) % 2 != 0

def main(argv=None):
    token = utils.get_github_api_accesstoken()
    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases', org, repository)
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    major_dict = {}
    release_dict = {}
    image_dict = {}
    latest_link_dict = {}
    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())

    for release in response:
        version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])

        if version is None or os_ext:
            continue

        if major in major_dict and major_dict[major] != release['prerelease']:
            continue

        major_dict[major] = release['prerelease']
        assets = release['assets']

        if release['prerelease'] is not True and major not in latest_link_dict:
            latest_link_dict[major] = Template(latest_template).substitute(
                major=major,
                url = release['html_url']
            )

        for asset in assets:
            match = asset_pattern.match(asset['name'])

            if match is not None:
                asset_image_type = match.group(1)

                if asset_image_type == 'jdk':
                    asset_os = match.group(3)
                    tag = release['name']
                    image_is_lts = is_lts(major) and not release['prerelease']

                    if major not in image_dict:
                        image_dict[major] = {
                            'label': str.format('SapMachine {0}', major),
                            'lts': image_is_lts,
                            'ea': release['prerelease']
                        }

                    if major in release_dict:
                        releases = release_dict[major]
                    else:
                        releases = Releases(major)
                        release_dict[major] = releases

                    release_dict[major].add_asset(asset['browser_download_url'], asset_os, tag)

    latest_lts_version = 0

    for major in image_dict:
        if image_dict[major]['lts'] and int(major) > latest_lts_version:
            latest_lts_version = int(major)

    json_root = {
        'imageTypes':[],
        'os':[],
        'assets':{}
    }

    for major in sorted(image_dict):
        if int(major) > latest_lts_version or image_dict[major]['lts']:
            json_root['imageTypes'].append({'id': major, 'label': image_dict[major]['label'], 'lts': image_dict[major]['lts'], 'ea': image_dict[major]['ea']})
        else:
            del image_dict[major]

    def get_os_key(os):
        return os_description[os]['ordinal']

    for os in sorted(os_description, key=get_os_key):
        json_root['os'].append({'key': os, 'value': os_description[os]['name'], 'ordinal': os_description[os]['ordinal']})

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

    return 0

if __name__ == "__main__":
    sys.exit(main())
