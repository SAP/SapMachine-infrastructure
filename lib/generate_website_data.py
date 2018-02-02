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
    git_user = os.environ['GIT_USER']
    git_password = os.environ['GIT_PASSWORD']
    repo = str.format('https://{0}:{1}@github.com/SAP/SapMachine.git', git_user, git_password)
    branch = 'gh-pages'
    local_repo = join(os.getcwd(), 'gh-pages')

    utils.remove_if_exists(local_repo)

    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']

    utils.run_cmd(['git', 'clone', '-b', branch, repo, local_repo])

    with open(join(local_repo, 'assets', 'data', 'sapmachine_releases.json'), 'w+') as sapmachine_releases:
        sapmachine_releases.write(data)

    utils.run_cmd(['git', 'add', 'assets'], cwd=local_repo)
    utils.run_cmd(['git', 'commit', '-m', 'Updated release data.'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'fetch'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'rebase'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'push'], cwd=local_repo, env=env)

    utils.remove_if_exists(local_repo)

def main(argv=None):
    token = utils.get_github_api_accesstoken()
    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases', org, repository)
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    releases_dict = {}
    image_type_dict = {}
    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())
    for release in response:
        if release['prerelease'] is True:
            continue

        version, major, build_number, sap_build_number = utils.sapmachine_tag_components(release['name'])
        assets = release['assets']

        for asset in assets:
            match = asset_pattern.match(asset['name'])

            if match is not None:
                asset_image_type = match.group(1)
                asset_os = match.group(3)
                image_type = major + '-' + asset_image_type
                tag = release['name']

                if image_type not in image_type_dict:
                    image_type_dict[image_type] = str.format('SapMachine {0} {1}', major, asset_image_type)

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

if __name__ == "__main__":
    sys.exit(main())
