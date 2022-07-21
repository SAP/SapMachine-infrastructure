'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import json
import os
import re
import sys
import utils

from os.path import join
from string import Template
from versions import SapMachineTag

sapMachinePushURL= str.format('https://{0}:{1}@github.com/SAP/SapMachine.git',
    os.environ['GIT_USER'], os.environ['GIT_PASSWORD'])

os_description = {
    'linux-ppc64le':           { 'ordinal': 1, 'name': 'Linux ppc64le' },
    'linux-x64':               { 'ordinal': 2, 'name': 'Linux x64' },
    'linux-aarch64':           { 'ordinal': 3, 'name': 'Linux aarch64' },
    'macos-x64':               { 'ordinal': 4, 'name': 'MacOS x64'},
    'macos-x64-installer':     { 'ordinal': 5, 'name': 'MacOS x64 Installer'},
    'macos-aarch64':           { 'ordinal': 6, 'name': 'MacOS aarch64'},
    'macos-aarch64-installer': { 'ordinal': 7, 'name': 'MacOS aarch64 Installer'},
    'windows-x64':             { 'ordinal': 8, 'name': 'Windows x64'},
    'windows-x64-installer':   { 'ordinal': 9, 'name': 'Windows x64 Installer'}
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

class SapMachineMajorVersion:
    def __init__(self, major):
        self.major = major
        self.lts = utils.sapmachine_is_lts(major)
        self.release = None
        self.prerelease = None

    def is_released(self):
        return self.release is not None

    def is_lts(self):
        return self.lts

    def get_release_object_to_update_if_tag_is_newer(self, tag, prerelease, url):
        if (prerelease):
            if self.prerelease is None or tag.is_greater_than(self.prerelease.tag):
                self.prerelease = Release(tag, url)
                return self.prerelease
        else:
            if self.release is None or tag.is_greater_than(self.release.tag):
                self.release = Release(tag, url)
                return self.release

        return None

    def add_to_release_json(self, json_root):
        if self.release is not None:
            json_root['majors'].append({'id': str(self.major), 'label': str.format('SapMachine {0}', self.major), 'lts': self.lts, 'ea': False})
            json_root['assets'][self.major] = self.release.to_release_json()

        if self.prerelease is not None:
            id = str(self.major) + "-ea"
            json_root['majors'].append({'id': id, 'label': str.format('SapMachine {0}', self.major), 'lts': self.lts, 'ea': True})
            json_root['assets'][id] = self.prerelease.to_release_json()

class Release:
    def __init__(self, tag, url):
        self.tag = tag
        self.url = url
        self.assets = {}

    def add_asset(self, image_type, os, asset_url):
        if image_type not in self.assets:
            self.assets[image_type] = {}

        self.assets[image_type][os] = asset_url

    def to_release_json(self):
        json_root = {
            'releases': []
        }
        release_json = {
            'tag': self.tag.as_string()
        }
        for image_type in self.assets:
            release_json[image_type] = {}
            for os in self.assets[image_type]:
                release_json[image_type][os] = self.assets[image_type][os]
        json_root['releases'].append(release_json)
        return json_root

def push_to_git(files):
    local_repo = join(os.getcwd(), 'gh-pages')
    if not os.path.exists(local_repo):
        utils.run_cmd("git clone --branch gh-pages --single-branch https://github.com/SAP/SapMachine.git gh-pages".split(' '))
    else:
        utils.run_cmd("git pull origin gh-pages".split(' '), cwd=local_repo)

    commits = False
    for _file in files:
        location = join(local_repo, _file['location'])
        if not os.path.exists(os.path.dirname(location)):
            os.makedirs(os.path.dirname(location))
        with open(location, 'w+') as out:
            out.write(_file['data'])
        _, diff, _  = utils.run_cmd("git diff".split(' '), cwd=local_repo, std=True)
        if diff.strip():
            utils.git_commit(local_repo, _file['commit_message'], [location])
            commits = True

    if commits:
        utils.run_cmd(str.format('git push {0}', sapMachinePushURL).split(' '), cwd=local_repo)

def main(argv=None):
    print("Querying GitHub for SapMachine releases...")
    sys.stdout.flush()
    releases = utils.get_github_releases()
    print("Done.")

    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    release_dict = {}
    for release in releases:
        sapMachineTag = SapMachineTag.from_string(release['name'])

        if sapMachineTag is None:
            print(str.format("{0} is no SapMachine release, dropping", release['name']))
            continue

        major = sapMachineTag.get_major()
        if not major in release_dict:
            sapMachineVersion = SapMachineMajorVersion(major)
            release_dict[major] = sapMachineVersion
        else:
            sapMachineVersion = release_dict[major]

        sapMachineRelease = sapMachineVersion.get_release_object_to_update_if_tag_is_newer(sapMachineTag, release['prerelease'], release['html_url'])

        if sapMachineRelease is None:
            continue

        for asset in release['assets']:
            match = asset_pattern.match(asset['name'])

            if match is None:
                continue

            image_type = match.group(1)
            os = match.group(3)
            file_type = match.group(4)

            if os == 'windows-x64' and file_type == '.msi':
                os = 'windows-x64-installer'

            if os == 'macos-x64' or os == 'osx-x64':
                if file_type == '.dmg':
                    os = 'macos-x64-installer'
                else:
                    os = 'macos-x64'

            if os == 'macos-aarch64' or os == 'osx-aarch64':
                if file_type == '.dmg':
                    os = 'macos-aarch64-installer'
                else:
                    os = 'macos-aarch64'

            sapMachineRelease.add_asset(image_type, os, asset['browser_download_url'])

    # reduce releases dictionary by removing obsolete versions
    # Keep LTS versions, latest release and the release that is currently in development
    latest_released_version = 0
    for major in list(release_dict.keys()):
        if not release_dict[major].is_released():
            continue
        if major > latest_released_version:
            if latest_released_version > 0 and not release_dict[latest_released_version].is_lts():
                del release_dict[latest_released_version]
            latest_released_version = major
        elif not release_dict[major].is_lts():
            del release_dict[major]

    json_root = {
        'majors':[],
        'imageTypes':[],
        'os':[],
        'assets':{}
    }

    release_dict = dict(sorted(release_dict.items(), key = lambda x:x[0], reverse = True))

    for major in release_dict:
        release_dict[major].add_to_release_json(json_root)

    for image_type in image_type_description:
        json_root['imageTypes'].append({'key': image_type, 'value': image_type_description[image_type]['name'], 'ordinal': image_type_description[image_type]['ordinal']})

    for os in os_description:
        json_root['os'].append({'key': os, 'value': os_description[os]['name'], 'ordinal': os_description[os]['ordinal']})

    files = [{
        'location': join('assets', 'data', 'sapmachine_releases.json'),
        'data': json.dumps(json_root, indent=4) + '\n',
        'commit_message': 'Updated release data.'
    }]

    for major in release_dict:
        if not release_dict[major].is_released():
            continue

        files.append({
            'location': join('latest', str(major), 'index.md'),
            'data': Template(latest_template).substitute(
                major = major,
                url = release_dict[major].release.url
            ),
            'commit_message': str.format('Updated latest link for SapMachine {0}', major)
        })

    push_to_git(files)

    return 0

if __name__ == "__main__":
    sys.exit(main())
