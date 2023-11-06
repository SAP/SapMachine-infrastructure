'''
Copyright (c) 2018-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import json
import os
import re
import sys
import utils

from enum import Enum
from os.path import join
from string import Template
from urllib.request import urlopen, Request
from urllib.error import HTTPError
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
    'windows-x64-installer':   { 'ordinal': 9, 'name': 'Windows x64 Installer'},
    'aix-ppc64':               { 'ordinal': 10, 'name': 'AIX'}
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

latest_template_download = '''---
layout: default
title: Latest SapMachine ${major} Release for ${platform}
checksum: ${checksum}
redirect_to:
  - ${url}
---
'''

class FileOperation(Enum):
    ADD_FILE = 1
    REMOVE_DIR = 2


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
        self.checksums = {}

    def add_asset(self, image_type, os, asset_url):
        if image_type not in self.assets:
            self.assets[image_type] = {}

        self.assets[image_type][os] = asset_url

    def add_checksum(self, image_type, os, checksum):
        if image_type not in self.checksums:
            self.checksums[image_type] = {}

        self.checksums[image_type][os] = checksum

    def to_release_json(self):
        json_root = {
            'releases': [],
            'checksums': []
        }
        release_json = {
            'tag': self.tag.as_string()
        }
        for image_type in self.assets:
            release_json[image_type] = {}
            for os in self.assets[image_type]:
                release_json[image_type][os] = self.assets[image_type][os]
        json_root['releases'].append(release_json)

        checksum_json = {
            'tag': self.tag.as_string()
        }
        for image_type in self.checksums:
            checksum_json[image_type] = {}
            for os in self.checksums[image_type]:
                checksum_json[image_type][os] = self.checksums[image_type][os]
        json_root['checksums'].append(checksum_json)

        return json_root

def push_to_git(files):
    local_repo = join(os.getcwd(), 'gh-pages')
    if not os.path.exists(local_repo):
        utils.run_cmd("git clone --branch gh-pages --single-branch https://github.com/SAP/SapMachine.git gh-pages".split(' '))
    else:
        utils.run_cmd("git pull origin gh-pages".split(' '), cwd=local_repo)

    addFile = False
    commits = False
    for _file in files:
        location = join(local_repo, _file['location'])

        if _file['operation'] == FileOperation.ADD_FILE:
            if not os.path.exists(os.path.dirname(location)):
                os.makedirs(os.path.dirname(location))
            if not os.path.isfile(location):
                addFile = True
            with open(location, 'w+') as out:
                out.write(_file['data'])
            _, diff, _  = utils.run_cmd("git diff".split(' '), cwd=local_repo, std=True)
            if diff.strip():
                utils.git_commit(local_repo, _file['commit_message'], [_file['location']])
                commits = True
            elif addFile:
                utils.git_commit(local_repo, _file['commit_message'], [location])
                commits = True

        elif _file['operation'] == FileOperation.REMOVE_DIR:
            if os.path.exists(location):
                print("remove dir: ", _file['commit_message'])
                utils.run_cmd(['git', 'rm', '-r', _file['location']], cwd=local_repo, std=True)

    if commits:
        utils.run_cmd(str.format('git push {0}', sapMachinePushURL).split(' '), cwd=local_repo)

def sapmachine_checksum_pattern():
    return utils.sapmachine_asset_base_pattern() + '(|\.msi\.|\.dmg\.|\.)(sha256\.txt)$'

def main(argv=None):
    print("Querying GitHub for SapMachine releases...")
    sys.stdout.flush()
    releases = utils.get_github_releases()
    print("Done.")

    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    checksum_pattern = re.compile(sapmachine_checksum_pattern())

    release_dict = {}
    for release in releases:
        sapMachineTag = SapMachineTag.from_string(release['name'])

        if sapMachineTag is None:
            print(str.format("{0} is no SapMachine release, dropping", release['name']))
            continue

        print(str.format("release: {0}", release['name']))

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
            print(str.format("\nfound asset: {0}", asset['name']))

            skipped = True
            if match is not None:

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

                print(str.format("  identified as downloadable file [ os: {0} - file type: {1} ] ", os, file_type))
                print("  url: " + asset['browser_download_url'])

                sapMachineRelease.add_asset(image_type, os, asset['browser_download_url'])
                skipped = False

            checksum_match = checksum_pattern.match(asset['name'])
            if checksum_match is not None:
                image_type = checksum_match.group(1)
                os = checksum_match.group(3)
                file_type2 = checksum_match.group(4)
                file_type = checksum_match.group(5)

                if os == 'windows-x64' and file_type2 == '.msi.':
                    os = 'windows-x64-installer'

                if os == 'macos-x64' or os == 'osx-x64':
                    if file_type2 == '.dmg.':
                        os = 'macos-x64-installer'
                    else:
                        os = 'macos-x64'

                if os == 'macos-aarch64' or os == 'osx-aarch64':
                    if file_type2 == '.dmg.':
                        os = 'macos-aarch64-installer'
                    else:
                        os = 'macos-aarch64'


                print(str.format("  identified as checksum file [ os: {0} - file type: {1} - sub file type: {2} ]", os, file_type, file_type2))
                print("  checksum url: " + asset['browser_download_url'])

                request = Request(asset['browser_download_url'])
                checksum = 0
                try:
                    response = urlopen(request)
                    response = response.read()
                    print("  found checksum: " + str(response[:64].decode()))
                    sapMachineRelease.add_checksum(image_type, os, "sha256 " + response[:64].decode())

                    skipped = False
                except HTTPError as httpError:
                    print("  checksum file couldn't be downloaded: " + str(httpError.code) + ": " + httpError.reason)

            if skipped:
                print("  skipped because not identified as archive or no checksum found")


    files = []

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
            files.append({
                'operation' : FileOperation.REMOVE_DIR,
                'location': join('latest', str(major)),
                'data': '',
                'commit_message': str.format('delete outdated latest link directory for SapMachine {0}.', major)
            })
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

    files.append({
        'operation' : FileOperation.ADD_FILE,
        'location': join('assets', 'data', 'sapmachine_releases.json'),
        'data': json.dumps(json_root, indent=4) + '\n',
        'commit_message': 'Updated release data.'
    })

    for major in release_dict:
        if not release_dict[major].is_released():
            continue

        files.append({
            'operation' : FileOperation.ADD_FILE,
            'location': join('latest', str(major), 'index.md'),
            'data': Template(latest_template).substitute(
                major = major,
                url = release_dict[major].release.url
            ),
            'commit_message': str.format('Updated latest link for SapMachine {0}', major)
        })

        for k in range(len(json_root['assets'][major]['releases'])):
            for imageType in list(json_root['assets'][major]['releases'][k]):
                if (imageType == "jdk" or imageType == "jre"):
                    for platform in list(json_root['assets'][major]['releases'][k][imageType]):

                        checksum = ""
                        try:
                            checksum = str(json_root['assets'][major]['checksums'][k][imageType][platform])
                        except KeyError:
                            checksum = "not available"
                            
                        files.append({
                            'operation' : FileOperation.ADD_FILE,
                            'location': join('latest', str(major), str(platform), str(imageType), 'index.md'),
                            'data': Template(latest_template_download).substitute(
                                major = major,
                                platform = str(platform),
                                checksum = str(checksum),
                                url = str(json_root['assets'][major]['releases'][k][imageType][platform])
                            ),
                            'commit_message': str.format('Updated latest link for SapMachine {0}, {1}/{2}', major, str(platform), str(imageType))
                        })

    push_to_git(files)

    return 0

if __name__ == "__main__":
    sys.exit(main())
