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

os_description = {
    'linux-x64': 'Linux x64 glibc',
    'linux-x64-musl': 'Linux x64 musl'
}

latest_template = '''---
layout: default
title: Latest SapMachine ${major} Release
redirect_to:
  - ${url}
---
'''

class Releases:
    def __init__(self, image_type):
        self.image_type = image_type
        self.releases = {}

    def add_asset(self, asset_url, os, tag):
        if tag not in self.releases:
            self.releases[tag] = {}

        self.releases[tag][os] = asset_url

    def transform(self):
        json_root = {
            self.image_type: {
                'releases': []
            }
        }

        for tag in sorted(self.releases, reverse=True):
            release = {
                'tag': tag
            }

            for os in self.releases[tag]:
                release[os] = self.releases[tag][os]

            json_root[self.image_type]['releases'].append(release)

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
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases', org, repository)
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    major_dict = {}
    releases_dict = {}
    image_type_dict = {}
    latest_link_dict = {}
    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())

    for release in response:
        version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])

        if version is None or os_ext:
            continue

        if major in major_dict:
            continue

        major_dict[major] = True
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
                asset_os = match.group(3)
                tag = release['name']
                image_type = major + '-' + asset_image_type

                if release['prerelease'] is True:
                    image_type += '-ea'

                if image_type not in image_type_dict:
                    image_type_dict[image_type] = str.format('SapMachine {0} {1}{2}',
                        major,
                        asset_image_type,
                        " (pre-release)" if release['prerelease'] else "")

                if image_type in releases_dict:
                    releases = releases_dict[image_type]
                else:
                    releases = Releases(image_type)
                    releases_dict[image_type] = releases

                releases_dict[image_type].add_asset(asset['browser_download_url'], asset_os, tag)

    json_root = {
        'imageTypes':[],
        'os':[],
        'assets':{}
    }

    for image_type in sorted(image_type_dict):
        json_root['imageTypes'].append({'key': image_type, 'value': image_type_dict[image_type]})

    for os in sorted(os_description):
        json_root['os'].append({'key': os, 'value': os_description[os]})

    for release in releases_dict:
        json_root['assets'].update(releases_dict[release].transform())

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

if __name__ == "__main__":
    sys.exit(main())
