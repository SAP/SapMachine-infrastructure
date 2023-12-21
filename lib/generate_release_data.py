'''
Copyright (c) 2018-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import json
import os
import re
import sys
import utils

from enum import Enum
from os.path import join
from string import Template
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from versions import SapMachineTag
from collections import OrderedDict

sapMachinePushURL= str.format('https://{0}:{1}@github.com/SAP/SapMachine.git',
    os.environ['GIT_USER'], os.environ['GIT_PASSWORD'])

imageTypes = [
    {"key": "jdk", "value": "JDK", "ordinal": 1},
    {"key": "jre", "value": "JRE", "ordinal": 2}
]

latest_overall_template = '''---
layout: default
title: Latest SapMachine Release
redirect_to:
  - ${url}
---
'''

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

    #if commits:
    #    utils.run_cmd(str.format('git push {0}', sapMachinePushURL).split(' '), cwd=local_repo)

# custom version comparator
def custom_version_comparator(item):
    version = list(map(int, item[0].split('.')))
    version.extend([0 for i in range(5 - len(version))])
    return version[0], version[1], version[2], version[3], version[4]

# custom tag comparator that moves ga builds on top
def custom_tags_comparator(item):
    tag = SapMachineTag.from_string(item[0])
    return 2 if tag.is_ga() else 1, tag.version[0], tag.version[1], tag.version[2], tag.version[3], tag.version[4], tag.get_build_number()

def lookup_or_create_build_dict_in_sapmachine_latest(buildtag, releases, checksums):
    # Lookup build dict
    d_release = None
    d_checksum = None
    for build_data in releases:
        if build_data['tag'] == buildtag:
            d_release = build_data
            break

    if d_release is None:
        d_release = {}
        d_release['tag'] = buildtag
        d_release['jdk'] = {}
        d_release['jre'] = {}
        releases.append(d_release)
        d_checksum = {}
        d_checksum['tag'] = buildtag
        d_checksum['jdk'] = {}
        d_checksum['jre'] = {}
        checksums.append(d_checksum)
        return d_release, d_checksum

    for build_data in checksums:
        if build_data['tag'] == buildtag:
            d_checksum = build_data
            break

    return d_release, d_checksum

def loop_through_build_assets(build, build_data, imageType, handled_platforms, releases, checksums):
    d_release = d_checksum = None
    for platform, archives in build_data['assets'][imageType].items():
        for archive_type, archive_data in archives.items():
            real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
            if real_platform in handled_platforms:
                continue

            # Lookup release and checksum dict for a build
            if d_release is None:
                d_release, d_checksum = lookup_or_create_build_dict_in_sapmachine_latest(build, releases, checksums)

            # insert info
            d_release[imageType][real_platform] = archive_data['url']
            if 'checksum' in archive_data:
                d_checksum[imageType][real_platform] = "sha256 " + archive_data['checksum']
            handled_platforms.add(real_platform)

def process_major_release(major_updates_data, assets, id, ea):
    releases = []
    checksums = []
    platforms_jdk = set()
    platforms_jre = set()
    for builds in major_updates_data:
        for build, build_data in builds.items():
            if build_data['ea'] != ('true' if ea else 'false'):
                continue
            loop_through_build_assets(build, build_data, 'jdk', platforms_jdk, releases, checksums)
            print(f"Build: {build}")
            loop_through_build_assets(build, build_data, 'jre', platforms_jre, releases, checksums)
    if releases:
        assets[id] = {'releases': releases, 'checksums': checksums}

class Generator:
    last_len = 0
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    checksum_pattern = re.compile(utils.sapmachine_checksum_pattern())

    def __init__(self, args):
        self.args = args

    def load_sapmachine_releases(self):
        # Load existing data or scratch
        self.all_releases = self.args.output + "-all.json"
        if self.args.scratch or not os.path.exists(self.all_releases):
            print(f"Creating release data files with prefix {self.args.output}.", end='')
            self.sm_releases = {}
        else:
            print(f"Updating release data files with prefix {self.args.output}.", end='')
            with open(self.all_releases, 'r') as file:
                self.sm_releases = json.load(file)

    def load_github_releases(self):
        # Load input data from GitHub or file
        if self.args.input_file is None:
            print(" Source: GitHub.")
            self.log_status(status_text="Querying GitHub API...")
            self.gh_releases = utils.github_api_request('releases', per_page=300)

            # Save data
            with open('github-releases.json', 'w') as output_file:
                json.dump(self.gh_releases, output_file, indent=2)

        else:
            print(f" Source: {self.args.input_file}.")
            with open(self.args.input_file, 'r') as file:
                self.gh_releases = json.load(file)
        self.number_of_releases = len(self.gh_releases)

    def log_status(self, text = None, status_text = None, done = False):
        if status_text is None:
            if not hasattr(self, 'tags') or self.tags is None:
                status_text = "Processing..."
            elif not hasattr(self, 'asset_name') or self.asset_name is None:
                status_text = f"Processing release {self.tags} ({self.release_count}/{self.number_of_releases})..."
            else:
                status_text = f"Processing release {self.tags} ({self.release_count}/{self.number_of_releases}): {self.asset_name}..."

        if text is None:
            new_len = len(status_text)
            status_text = status_text.ljust(self.last_len)
            self.last_len = new_len if done is False else 0
        else:
            text = text.ljust(self.last_len)
            self.last_len = len(status_text) if done is False else 0
            print(text)

        print(status_text, end = '\r' if done is False else None)

    def get_major(self, release):
        self.tags = release['tag_name']
        if self.tags is None:
            self.log_status(f"Release {release['html_url']} does not have a tag, skipping.")
            self.release_count += 1
            return

        self.log_status()

        tag = SapMachineTag.from_string(self.tags)
        self.majors.add(str(tag.get_major()))

    def do_release(self, release, restrict_major=None):
        self.tags = release['tag_name']
        if self.tags is None:
            self.log_status(f"Release {release['html_url']} does not have a tag, skipping.")
            self.release_count += 1
            return

        self.log_status()

        if not 'assets' in release or not isinstance(release['assets'], list) :
            self.log_status(f"Release {self.tags} has no assets, skipping.")
            self.release_count += 1
            return

        tag = SapMachineTag.from_string(self.tags)
        major = str(tag.get_major())

        if restrict_major is not None and major != restrict_major:
            self.release_count += 1
            return

        d_major = self.sm_releases.get(major, None)
        if d_major is None:
            d_major = {}
            d_major['lts'] = str(utils.sapmachine_is_lts(major)).lower()
            self.sm_releases[major] = d_major

        d_updates = d_major.get('updates', None)
        if d_updates is None:
            d_updates = {}
            d_major['updates'] = d_updates

        update = tag.get_version_string_without_build()
        d_update = d_updates.get(update, None)
        if d_update is None:
            d_update = {}
            d_updates[update] = d_update

        d_build = d_update.get(self.tags, None)
        if d_build is None or self.tags == self.args.reload_tag:
            d_build = {}
            d_update[self.tags] = d_build

        d_build['url'] = release['html_url']
        d_build['ea'] = str(tag.get_build_number() is not None).lower()

        d_assets = d_build.get('assets', None)
        if d_assets is None:
            d_assets = {}
            d_build['assets'] = d_assets

        d_jdks = d_assets.get('jdk', None)
        if d_jdks is None:
            d_jdks = {}
            d_assets['jdk'] = d_jdks
        d_jres = d_assets.get('jre', None)
        if d_jres is None:
            d_jres = {}
            d_assets['jre'] = d_jres

        for asset in release['assets']:
            self.asset_name = asset['name']
            self.log_status()

            is_asset = False
            match = self.asset_pattern.match(self.asset_name)
            checksum_match = self.checksum_pattern.match(self.asset_name)
            if match is not None:
                image_type = match.group(1)
                platform = match.group(3)
                is_asset = True
            elif checksum_match is not None:
                image_type = checksum_match.group(1)
                platform = checksum_match.group(3)
            elif 'symbols' in self.asset_name:
                if self.args.verbose:
                    self.log_status(f"Skipped {self.asset_name} because it is a symbol archive or checksum.")
                continue
            elif 'rpm' in self.asset_name:
                if self.args.verbose:
                    self.log_status(f"Skipped {self.asset_name} because it is an rpm archive or checksum.")
                continue
            else:
                self.log_status(f"Skipped {self.asset_name} because it is no viable archive or checksum.")
                continue

            if platform == 'osx-x64':
                platform = 'macos-x64'

            if platform == 'osx-aarch64':
                platform = 'macos-aarch64'

            if is_asset:
                if self.args.verbose:
                    self.log_status(f"{self.asset_name} is an archive file for {platform}.")
            else:
                if self.asset_name.endswith('dmg.sha256.txt') or self.asset_name.endswith('msi.sha256.txt'):
                    self.asset_name = self.asset_name[:-len('.sha256.txt')]
                elif self.asset_name.endswith('sha256.dmg.txt'):
                    self.asset_name = self.asset_name[:-len('.sha256.dmg.txt')] + '.dmg'
                elif self.asset_name.endswith('sha256.txt'):
                    self.asset_name = self.asset_name[:-len('.sha256.txt')] + ('.zip' if platform == 'windows-x64' else '.tar.gz')

            d_type = d_jdks if image_type == 'jdk' else d_jres if image_type == 'jre' else None
            if d_type is None:
                self.log_status(f"Image Type {image_type} is unknown.")
                continue

            if platform in d_type.keys():
                d_platform = d_type[platform]
            else:
                d_platform = {}
                d_type[platform] = d_platform

            if self.asset_name.endswith('tar.gz'):
                asset_type = 'tar.gz'
            elif self.asset_name.endswith('zip'):
                asset_type = 'zip'
            elif self.asset_name.endswith('msi'):
                asset_type = 'msi'
            elif self.asset_name.endswith('dmg'):
                asset_type = 'dmg'
            else:
                self.log_status(f"{self.asset_name} is an unsupported asset type.")
                continue

            if asset_type in d_platform:
                d_asset = d_platform[asset_type]
            else:
                d_asset = {}
                d_platform[asset_type] = d_asset

            if 'name' in d_asset:
                if d_asset['name'] != self.asset_name:
                    self.log_status(f"{self.asset_name} does not match existing name {d_asset['name']} of {self.tags}.")
                    break
            else:
                d_asset['name'] = self.asset_name

            if is_asset:
                d_asset['url'] = asset['browser_download_url']
            else:
                checksum = d_asset.get('checksum', None)
                if checksum is None:
                    request = Request(asset['browser_download_url'])
                    try:
                        response = urlopen(request)
                        response = response.read()
                        checksum = str(response[:64].decode())
                        if self.args.verbose:
                            self.log_status(f"Downloaded checksum for {self.asset_name}: {checksum}")

                        d_asset['checksum'] = checksum

                    except HTTPError as httpError:
                        self.log_status(f"Checksum file for {self.asset_name} could not be downloaded from {asset['browser_download_url']}: {httpError.code} ({httpError.reason})")

        if not d_jdks:
            del d_assets['jdk']
        if not d_jres:
            del d_assets['jre']

        # if we just update data, we return here.
        # otherwise we better save data after every release to allow for interruption
        self.release_count += 1
        if not self.args.scratch:
            return

        # sort updates
        d_updates = dict(sorted(d_updates.items(), key=custom_version_comparator, reverse=True))
        d_major['updates'] = d_updates

        # sort builds, use custom comparator that moves ga builds on top
        d_update = dict(sorted(d_update.items(), key=custom_tags_comparator, reverse=True))
        d_updates[update] = d_update

        # Save data to files
        with open(self.all_releases, 'w') as output_file:
            json.dump(self.sm_releases, output_file, indent=2)

        major_releases = self.args.output + f"-{major}.json"
        with open(major_releases, 'w') as output_file:
            json.dump(d_major, output_file, indent=2)

    def get_majors(self):
        self.release_count = 1
        self.majors = set()
        for release in self.gh_releases:
            self.get_major(release)

        print(f"Majors found: {sorted(self.majors)}")

    def iterate_releases(self):
        self.release_count = 1
        if self.args.major is not None:
            if self.args.major in self.majors:
                for release in self.gh_releases:
                    self.do_release(release, self.args.major)
            else:
                print(f"Major version {self.args.major} does not exist.")
        else:
            for release in self.gh_releases:
                self.do_release(release)

        self.log_status(status_text="Done processing releases.", done=True)

        # when we had rebuilt from scratch, we can leave here. Otherwise we have to sort and save
        if self.args.scratch:
            return

        # sort majors
        self.sm_releases = dict(sorted(self.sm_releases.items(), reverse=True))

        # sort releases and save each one
        for major in self.majors:
            # sort updates
            d_updates = dict(sorted(self.sm_releases[major]['updates'].items(), key=custom_version_comparator, reverse=True))
            self.sm_releases[major]['updates'] = d_updates

            # sort builds, use custom comparator that moves ga builds on top
            for update, d_update in d_updates.items():
                d_update = dict(sorted(d_update.items(), key=custom_tags_comparator, reverse=True))
                d_updates[update] = d_update

            # save release
            major_releases = self.args.output + f"-{major}.json"
            with open(major_releases, 'w') as output_file:
                json.dump(self.sm_releases[major], output_file, indent=2)

        # Save all data
        with open(self.all_releases, 'w') as output_file:
            json.dump(self.sm_releases, output_file, indent=2)

    def generate_sapmachine_releases_json(self):
        majors = []
        assets = OrderedDict()
        for major in utils.sapmachine_dev_releases():
            id = str(major) + "-ea"
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True})
            print(f"Id: {id}")
            process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, True)

        for major in utils.sapmachine_active_releases():
            id = str(major) + "-ea"
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True})
            process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, True)
            id = str(major)
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': False})
            process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, False)

        json_root = {}
        json_root['majors'] = majors
        json_root['imageTypes'] = imageTypes
        json_root['assets'] = assets

        # Save data
        #with open('sapmachine-latest.json', 'w') as output_file:
        #    json.dump(json_root, output_file, indent=2)
        push_to_git([{
            'operation': FileOperation.ADD_FILE,
            'location': join('assets', 'data', 'sapmachine_releases.json'),
            'data': json.dumps(json_root, indent=2) + '\n',
            'commit_message': 'Update release data'
        }])

    def create_latest_links(self):
        files = []
        wrote_latest = False
        for major in self.majors:
            if int(major) in utils.sapmachine_active_releases():
                latest_data = None
                for builds in self.sm_releases[major]['updates'].values():
                    for tag_data in builds.values():
                        if tag_data['ea'] != 'true':
                            latest_data = tag_data
                            break
                    if latest_data is not None:
                        break

                if latest_data is None:
                    break

                if not wrote_latest:
                    files.append({
                        'operation': FileOperation.ADD_FILE,
                        'location': join('latest', 'index.md'),
                        'data': Template(latest_overall_template).substitute(url = latest_data['url']),
                        'commit_message': f"Update latest link for SapMachine"
                    })
                    wrote_latest = True

                files.append({
                    'operation': FileOperation.ADD_FILE,
                    'location': join('latest', major, 'index.md'),
                    'data': Template(latest_template).substitute(major = major,url = latest_data['url']),
                    'commit_message': f"Update latest link for SapMachine {major}"
                })

                for platform, archives in latest_data['assets']['jdk'].items():
                    for archive_type, archive_data in archives.items():
                        real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
                        files.append({
                            'operation': FileOperation.ADD_FILE,
                            'location': join('latest', major, real_platform, 'jdk', 'index.md'),
                            'data': Template(latest_template_download).substitute(
                                major = major,
                                platform = real_platform,
                                checksum = 'sha256 ' + archive_data['checksum'],
                                url = archive_data['url']
                            ),
                            'commit_message': f"Update latest link for SapMachine {major}, {real_platform}/jdk"
                        })

                for platform, archives in latest_data['assets']['jre'].items():
                    for archive_type, archive_data in archives.items():
                        real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
                        files.append({
                            'operation': FileOperation.ADD_FILE,
                            'location': join('latest', major, real_platform, 'jre', 'index.md'),
                            'data': Template(latest_template_download).substitute(
                                major = major,
                                platform = real_platform,
                                checksum = 'sha256 ' + archive_data['checksum'],
                                url = archive_data['url']
                            ),
                            'commit_message': f"Update latest link for SapMachine {major}, {real_platform}/jre"
                        })

            elif os.path.exists(join('latest', major)):
                files.append({
                    'operation': FileOperation.REMOVE_DIR,
                    'location': join('latest', major),
                    'data': '',
                    'commit_message': f"Delete outdated latest link directory for SapMachine {major}"
                })

        push_to_git(files)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', choices=['files', 'github'], default='files', help='output target, either "files" or "github". The latter means that changes are pushed to their location in SapMachine GitHub repo, branch gh-pages. Default is "files"', metavar='OUTPUT_TARGET')
    parser.add_argument('--output_prefix', default='sapmachine-releases', help='file name prefix to generate output files containing SapMachine release information. Only used when "--output files" is set. Default is "sapmachine-releases"', metavar='OUTPUT_PREFIX')
    parser.add_argument('-i', '--input', choices=['github', 'files'], default='github', help='input source, can be either "github" or "files". Default is "github". For "files", an input file is needed that contains the results of the GitHub Release API call in json format. The default name would be "github-releases.json" and can be modified with option "--input_file"', metavar='INPUT_SOURCE')
    parser.add_argument('--input_file', default='github-releases.json', help='input file that contains the results of the GitHub Release API call in json format (optional)', metavar='INPUT_FILE')
    parser.add_argument('-m', '--major', help='rebuild data for a certain major version, e.g. "21", "17"...', metavar='MAJOR')
    parser.add_argument('-u', '--update', help='rebuild data for a certain update version, e.g. "21", "17.0.3"...', metavar='UPDATE')
    parser.add_argument('-t', '--tag', help='rebuild data for a certain release/build, e.g. "sapmachine-17", "sapmachine-11.0.18", "sapmachine-22+26", ... In that case, GitHub Release information is queried only for the specified tag', metavar='TAG')
    parser.add_argument('-s', '--scratch_data', action='store_true', help='Clear existing release data and rebuild everything. The default is to update existing data. Does not work in conjunction with "--tag"')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode')
    args = parser.parse_args()

    generator = Generator(args)

    generator.load_sapmachine_releases()

    generator.load_github_releases()

    generator.get_majors()

    generator.iterate_releases()

    generator.generate_sapmachine_releases_json()

    generator.create_latest_links()

    return 0

if __name__ == "__main__":
    sys.exit(main())
