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

os_description = {
    'linux-x64': 'Linux x64 glibc',
    'linux-x64-musl': 'Linux x64 musl'
}

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

def push_to_git(data):
    local_repo = join(os.getcwd(), 'gh-pages')
    utils.git_clone('github.com/SAP/SapMachine.git', 'gh-pages', local_repo)

    with open(join(local_repo, 'assets', 'data', 'sapmachine_releases.json'), 'w+') as sapmachine_releases:
        sapmachine_releases.write(data)

    utils.git_commit(local_repo, 'Updated release data.', ['assets'])
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
    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())
    for release in response:
        # switch back on when when 10 is released
        # if release['prerelease'] is True:
        #    continue

        version, version_part, major, build_number, sap_build_number = utils.sapmachine_tag_components(release['name'])

        if major in major_dict:
            continue

        major_dict[major] = True

        assets = release['assets']

        if version is None:
            continue

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

    push_to_git(json.dumps(json_root, indent=4))
    #with open('test.json', 'w') as test_out:
    #    test_out.write(json.dumps(json_root, indent=4))

if __name__ == "__main__":
    sys.exit(main())
