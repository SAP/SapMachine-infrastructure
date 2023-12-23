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
from shutil import rmtree
from string import Template
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from versions import SapMachineTag
from collections import OrderedDict

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

# custom version comparator
def custom_version_comparator(item):
    version = list(map(int, item[0].split('.')))
    version.extend([0 for i in range(5 - len(version))])
    return version[0], version[1], version[2], version[3], version[4]

# custom tag comparator that moves ga builds on top
def custom_tags_comparator(item):
    tag = SapMachineTag.from_string(item[0])
    return 2 if tag.is_ga() else 1, tag.version[0], tag.version[1], tag.version[2], tag.version[3], tag.version[4], tag.get_build_number()

class Loggerich:
    last_len = 0

    def __init__(self, args):
        self.args = args

    def log_status(self, text):
        if self.args.no_status:
            return
        if self.last_len == 0:
            self.status_text = text
            self.last_len = len(self.status_text)
        else:
            self.status_text = text.ljust(self.last_len)
            self.last_len = len(text)

        print(self.status_text, end = '\r', flush=True)

    def clear_status(self):
        if self.last_len > 0:
            self.status_text = "".ljust(self.last_len)
            self.last_len = 0
            print(self.status_text, end = '\r')

    def log(self, text):
        if self.last_len == 0:
            print(text, flush=True)
        else:
            text = text.ljust(self.last_len)
            print(text)
            print(self.status_text, end='\r', flush=True)

class Generator:
    last_len = 0
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    checksum_pattern = re.compile(utils.sapmachine_checksum_pattern())

    def __init__(self, args):
        self.args = args
        self.loggerich = Loggerich(args)

    def setup_git(self):
        self.loggerich.log_status("Syncing GitHub SapMachine/gh-pages...")
        self.local_repo = join(os.getcwd(), 'gh-pages')
        if not os.path.exists(self.local_repo):
            rc, out, err = utils.run_cmd("git clone --branch gh-pages --single-branch https://github.com/SAP/SapMachine.git gh-pages".split(' '), std=True, quiet=True)
            if rc != 0:
                self.loggerich.clear_status()
                self.loggerich.log(f"Error cloning git repo. stdout:\n{out}\nstderr:\n{err}")
                sys.exit(-1)
        else:
            rc, out, err = utils.run_cmd("git fetch origin gh-pages".split(' '), cwd=self.local_repo, std=True, quiet=True)
            if rc != 0:
                self.loggerich.clear_status()
                self.loggerich.log(f"Error fetching git repo. stdout:\n{out}\nstderr:\n{err}")
                sys.exit(-1)
            rc, out, err = utils.run_cmd("git reset --hard origin/gh-pages".split(' '), cwd=self.local_repo, std=True, quiet=True)
            if rc != 0:
                self.loggerich.clear_status()
                self.loggerich.log(f"Error resetting git repo. stdout:\n{out}\nstderr:\n{err}")
                sys.exit(-1)

        self.loggerich.log("Synced GitHub SapMachine/gh-pages")
        self.loggerich.clear_status()

    def update_status(self):
        if not hasattr(self, 'cur_tag') or self.cur_tag is None:
            status_text = "Processing..."
        elif not hasattr(self, 'asset_name') or self.asset_name is None:
            status_text = f"Processing release {self.cur_tag} ({self.release_count}/{self.number_of_releases})..."
        else:
            status_text = f"Processing release {self.cur_tag} ({self.release_count}/{self.number_of_releases}): {self.asset_name}..."

        self.loggerich.log_status(status_text)

    # Load sapmachine release data according to options
    def load_sapmachine_release_data(self):
        if self.args.output == 'files':
            self.output_dir = os.getcwd()
            self.output_dir_latest = self.output_dir
        else:
            self.output_dir = join(self.local_repo, 'assets', 'data')
            self.output_dir_latest = self.local_repo
        self.all_releases_file = join(self.output_dir, self.args.output_prefix + "-all.json")

        # Check if we need or have to start completely from scratch
        self.scratch_all = self.args.scratch_data and self.args.major is None and self.args.update is None and self.args.tag is None
        if not os.path.exists(self.all_releases_file) or (self.scratch_all):
            if self.args.output == 'git':
                self.loggerich.log(f"Creating release data files in git repository ({self.output_dir}), prefix: {self.args.output_prefix}.")
            else:
                self.loggerich.log(f"Creating release data files in {self.output_dir}, prefix: {self.args.output_prefix}.")
            self.sm_releases = {}
            return

        # Load existing data
        if self.args.output == 'git':
            self.loggerich.log(f"Updating release data files in git repository ({self.output_dir}), prefix: {self.args.output_prefix}.")
        else:
            self.loggerich.log(f"Updating release data files in {self.output_dir}, prefix: {self.args.output_prefix}.")
        with open(self.all_releases_file, 'r') as file:
            self.sm_releases = json.load(file)

        # Clear out data of particular major, update or tag, if requested
        if self.args.major is not None:
            self.major = self.args.major
            if self.args.scratch_data:
                if self.major in self.sm_releases:
                    del self.sm_releases[self.major]
                    self.loggerich.log(f"Removed previous data for major release \"{self.major}\".")
                else:
                    self.loggerich.log(f"Major release \"{self.major}\" not found in data.")

        if self.args.update is not None:
            self.major = str(list(map(int, self.args.update.split('.')))[0])
            if self.args.scratch_data:
                if self.major in self.sm_releases:
                    if 'updates' in self.sm_releases[self.major] and self.args.update in self.sm_releases[self.major]['updates']:
                        del self.sm_releases[self.major]['updates'][self.args.update]
                        self.loggerich.log(f"Removed previous data for update release \"{self.args.update}\".")
                    else:
                        self.loggerich.log(f"Update {self.args.update} not found in data.")
                else:
                    self.loggerich.log(f"Major release \"{self.major}\" for update {self.args.update} not found in data.")

        if self.args.tag is not None:
            tag = SapMachineTag.from_string(self.args.tag)
            self.major = str(tag.get_major())
            if self.args.scratch_data:
                if self.major in self.sm_releases:
                    update = tag.get_version_string_without_build()
                    if 'updates' in self.sm_releases[self.major] and update in self.sm_releases[self.major]['updates']:
                        if self.args.tag in self.sm_releases[self.major]['updates'][update]:
                            del self.sm_releases[self.major]['updates'][update][self.args.tag]
                            self.loggerich.log(f"Removed previous data for tag \"{self.args.tag}\".")
                        else:
                            self.loggerich.log(f"Tag {self.args.tag} not found in data.")
                    else:
                        self.loggerich.log(f"Update {update} for tag {self.args.tag} not found in data.")
                else:
                    self.loggerich.log(f"Major release \"{self.major}\" for tag {self.args.tag} not found in data.")

    def load_github_release_data(self):
        if self.args.input == 'github':
            # Load input data from GitHub and store to file
            self.loggerich.log("Data Source: GitHub.")
            if self.args.tag is None:
                self.loggerich.log_status("Querying GitHub API...")
                self.gh_releases = utils.github_api_request('releases', per_page=300)
                if self.args.store_github_data:
                    self.loggerich.log_status(f"Storing results to {self.args.github_data_file}...")
                    with open(self.args.github_data_file, 'bw') as output_file:
                        output_file.write(json.dumps(self.gh_releases, indent=2).encode('utf-8'))
            else:
                self.loggerich.log_status("Querying GitHub API...")
                self.gh_releases = [utils.github_api_request(f"releases/tags/{self.args.tag}")]
                self.loggerich.log(f"Loaded release {self.args.tag} from GitHub")
            self.loggerich.clear_status()
        else:
            # Load input data from file
            self.loggerich.log(f"Data Source: {self.args.github_data_file}.")
            if not os.path.exists(self.args.github_data_file):
                self.loggerich.log(f"File {self.args.github_data_file} does not exist.")
                sys.exit(-1)
            with open(self.args.github_data_file, 'r') as file:
                self.gh_releases = json.load(file)

        # count some data
        self.release_count = 1
        self.number_of_releases = len(self.gh_releases)
        self.majors_in_gh_data = set()
        for release in self.gh_releases:
            self.cur_tag = release['tag_name']
            if self.cur_tag is None:
                self.loggerich.log(f"Release {release['html_url']} does not have a tag, skipping.")
                continue
            self.majors_in_gh_data.add(str(SapMachineTag.from_string(self.cur_tag).get_major()))
        self.majors_in_gh_data = sorted(self.majors_in_gh_data)
        self.loggerich.log(f"Major versions on GitHub: {self.majors_in_gh_data}")

    def do_release(self, release, restrict_major=None):
        self.cur_tag = release['tag_name']
        if self.cur_tag is None:
            self.loggerich.log(f"Release {release['html_url']} does not have a tag, skipping.")
            self.release_count += 1
            return

        self.update_status()

        if not 'assets' in release or not isinstance(release['assets'], list) :
            self.loggerich.log(f"Release {self.cur_tag} has no assets, skipping.")
            self.release_count += 1
            return

        tag = SapMachineTag.from_string(self.cur_tag)
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

        d_build = d_update.get(self.cur_tag, None)
        if d_build is None:
            d_build = {}
            d_update[self.cur_tag] = d_build

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
            self.update_status()

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
                    self.loggerich.log(f"Skipped {self.asset_name} because it is a symbol archive or checksum.")
                continue
            elif 'rpm' in self.asset_name:
                if self.args.verbose:
                    self.loggerich.log(f"Skipped {self.asset_name} because it is an rpm archive or checksum.")
                continue
            else:
                self.loggerich.log(f"Skipped {self.asset_name} because it is no viable archive or checksum.")
                continue

            if platform == 'osx-x64':
                platform = 'macos-x64'

            if platform == 'osx-aarch64':
                platform = 'macos-aarch64'

            if is_asset:
                if self.args.verbose:
                    self.loggerich.log(f"{self.asset_name} is an archive file for {platform}.")
            else:
                if self.asset_name.endswith('dmg.sha256.txt') or self.asset_name.endswith('msi.sha256.txt'):
                    self.asset_name = self.asset_name[:-len('.sha256.txt')]
                elif self.asset_name.endswith('sha256.dmg.txt'):
                    self.asset_name = self.asset_name[:-len('.sha256.dmg.txt')] + '.dmg'
                elif self.asset_name.endswith('sha256.txt'):
                    self.asset_name = self.asset_name[:-len('.sha256.txt')] + ('.zip' if platform == 'windows-x64' else '.tar.gz')

            d_type = d_jdks if image_type == 'jdk' else d_jres if image_type == 'jre' else None
            if d_type is None:
                self.loggerich.log(f"Image Type {image_type} is unknown.")
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
                self.loggerich.log(f"{self.asset_name} is an unsupported asset type.")
                continue

            if asset_type in d_platform:
                d_asset = d_platform[asset_type]
            else:
                d_asset = {}
                d_platform[asset_type] = d_asset

            if 'name' in d_asset:
                if d_asset['name'] != self.asset_name:
                    self.loggerich.log(f"{self.asset_name} does not match existing name {d_asset['name']} of {self.cur_tag}.")
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
                            self.loggerich.log(f"Downloaded checksum for {self.asset_name}: {checksum}")

                        d_asset['checksum'] = checksum

                    except HTTPError as httpError:
                        self.loggerich.log(f"Checksum file for {self.asset_name} could not be downloaded from {asset['browser_download_url']}: {httpError.code} ({httpError.reason})")

        if not d_jdks:
            del d_assets['jdk']
        if not d_jres:
            del d_assets['jre']

        # if we build up data from scratch, we should save here and there to allow for interruption
        if self.scratch_all and self.release_count % 10 == 0:
            with open(self.all_releases_file, 'bw') as output_file:
                output_file.write(json.dumps(self.sm_releases, indent=2).encode('utf-8'))

        self.release_count += 1

    def iterate_releases(self):
        self.release_count = 1
        if not hasattr(self, 'major'):
            for release in self.gh_releases:
                self.do_release(release)
        else:
            if self.major in self.majors_in_gh_data:
                for release in self.gh_releases:
                    self.do_release(release, self.major)
            else:
                self.loggerich.log(f"Major version {self.major} does not exist.")

        self.loggerich.log("Done processing releases.")
        self.loggerich.log_status("Sorting and saving release data...")

        # sort majors
        self.sm_releases = dict(sorted(self.sm_releases.items(), reverse=True))

        # sort and save data below each major
        for major in self.majors_in_gh_data if not hasattr(self, 'major') else [self.major]:
            # sort updates
            d_updates = dict(sorted(self.sm_releases[major]['updates'].items(), key=custom_version_comparator, reverse=True))
            self.sm_releases[major]['updates'] = d_updates

            # sort builds, use custom comparator that moves ga builds on top
            for update, d_update in d_updates.items():
                for build_data in d_update.values():
                    if 'assets' in build_data:
                        if 'jdk' in build_data['assets']:
                            build_data['assets']['jdk'] = dict(sorted(build_data['assets']['jdk'].items()))
                        if 'jre' in build_data['assets']:
                            build_data['assets']['jre'] = dict(sorted(build_data['assets']['jre'].items()))

                d_updates[update] = dict(sorted(d_update.items(), key=custom_tags_comparator, reverse=True))

            # save release
            release_file = join(self.output_dir, self.args.output_prefix + f"-{major}.json")
            with open(release_file, 'bw') as output_file:
                output_file.write(json.dumps(self.sm_releases[major], indent=2).encode('utf-8'))

        # save all releases
        with open(self.all_releases_file, 'bw') as output_file:
            output_file.write(json.dumps(self.sm_releases, indent=2).encode('utf-8'))

        self.loggerich.log("Sorted and saved release data.")
        self.loggerich.clear_status()

    def loop_through_build_assets_latest(self, build, build_data, handled_platforms_jdk, handled_platforms_jre, releases):
        jdks = {}
        for platform, archives in build_data['assets']['jdk'].items():
            for archive_type, archive_data in archives.items():
                real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
                if real_platform in handled_platforms_jdk:
                    continue

                # insert info
                jdks[real_platform] = {'url': archive_data['url'], 'checksum': "sha256 " + archive_data['checksum']}

                handled_platforms_jdk.add(real_platform)

        jres = {}
        for platform, archives in build_data['assets']['jre'].items():
            for archive_type, archive_data in archives.items():
                real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
                if real_platform in handled_platforms_jre:
                    continue

                # insert info
                jres[real_platform] = {'url': archive_data['url'], 'checksum': "sha256 " + archive_data['checksum']}

                handled_platforms_jre.add(real_platform)

        if not jdks and not jres:
            return
        d_build = {'tag': build}
        if jdks:
            d_build['jdk'] = jdks
        if jres:
            d_build['jre'] = jres
        releases.append(d_build)

    def process_major_release_latest(self, major_updates_data, d_major, ea):
        releases = []
        platforms_jdk = set()
        platforms_jre = set()
        for builds in major_updates_data:
            for build, build_data in builds.items():
                if build_data['ea'] != ('true' if ea else 'false'):
                    continue
                self.loop_through_build_assets_latest(build, build_data, platforms_jdk, platforms_jre, releases)
        if releases:
            d_major['releases'] = releases

    # generate a json file containing the latest supported versions
    def generate_sapmachine_releases_json_latest(self):
        self.loggerich.log_status(f"Creating {self.args.output_prefix}-latest.json...")
        json_root = OrderedDict()
        for major in utils.sapmachine_dev_releases():
            id = str(major) + "-ea"
            d_major = {'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True}
            self.process_major_release_latest(self.sm_releases[str(major)]['updates'].values(), d_major, True)
            json_root[id] = d_major

        for major in utils.sapmachine_active_releases():
            id = str(major) + "-ea"
            d_major = {'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True}
            self.process_major_release_latest(self.sm_releases[str(major)]['updates'].values(), d_major, True)
            json_root[id] = d_major
            id = str(major)
            d_major = {'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': False}
            self.process_major_release_latest(self.sm_releases[str(major)]['updates'].values(), d_major, False)
            json_root[id] = d_major

        with open(join(self.output_dir, self.args.output_prefix + f"-latest.json"), 'bw') as output_file:
            output_file.write(json.dumps(json_root, indent=2).encode('utf-8') + b'\n')

        self.loggerich.log(f"Created {self.args.output_prefix}-latest.json.")
        self.loggerich.clear_status()

    def lookup_or_create_build_dict_in_sapmachine_latest(self, buildtag, releases, checksums):
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
            if not checksums is None:
                d_checksum = {}
                d_checksum['tag'] = buildtag
                d_checksum['jdk'] = {}
                d_checksum['jre'] = {}
                checksums.append(d_checksum)
            return d_release, d_checksum

        if not checksums is None:
            for build_data in checksums:
                if build_data['tag'] == buildtag:
                    d_checksum = build_data
                    break

        return d_release, d_checksum

    def loop_through_build_assets(self, build, build_data, imageType, handled_platforms, releases, checksums):
        d_release = d_checksum = None
        for platform, archives in build_data['assets'][imageType].items():
            for archive_type, archive_data in archives.items():
                real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
                if real_platform in handled_platforms:
                    continue

                # Lookup release and checksum dict for a build
                if d_release is None:
                    d_release, d_checksum = self.lookup_or_create_build_dict_in_sapmachine_latest(build, releases, checksums)

                # insert info
                d_release[imageType][real_platform] = archive_data['url']
                if d_checksum is not None and 'checksum' in archive_data:
                    d_checksum[imageType][real_platform] = "sha256 " + archive_data['checksum']
                handled_platforms.add(real_platform)

    def process_major_release(self, major_updates_data, assets, id, ea, generate_checksums=False):
        releases = []
        checksums = [] if generate_checksums else None
        platforms_jdk = set()
        platforms_jre = set()
        for builds in major_updates_data:
            for build, build_data in builds.items():
                if build_data['ea'] != ('true' if ea else 'false'):
                    continue
                self.loop_through_build_assets(build, build_data, 'jdk', platforms_jdk, releases, checksums)
                self.loop_through_build_assets(build, build_data, 'jre', platforms_jre, releases, checksums)
        if releases:
            assets[id] = {'releases': releases, 'checksums': checksums} if generate_checksums else {'releases': releases}

    # generate a json file containing download information for the website
    def generate_sapmachine_releases_json_website(self):
        self.loggerich.log_status(f"Creating {self.args.output_prefix}-website.json...")
        majors = []
        assets = OrderedDict()
        for major in utils.sapmachine_dev_releases():
            id = str(major) + "-ea"
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True})
            self.process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, True)

        for major in utils.sapmachine_active_releases():
            id = str(major) + "-ea"
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True})
            self.process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, True)
            id = str(major)
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': False})
            self.process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, False)

        json_root = {}
        json_root['majors'] = majors
        json_root['imageTypes'] = imageTypes
        json_root['assets'] = assets

        with open(join(self.output_dir, self.args.output_prefix + f"-website.json"), 'bw') as output_file:
            output_file.write(json.dumps(json_root, indent=2).encode('utf-8') + b'\n')

        self.loggerich.log(f"Created {self.args.output_prefix}-website.json.")
        self.loggerich.clear_status()

    # generate the old sapmachine_releases.json. Deprecated, to be removed.
    def generate_sapmachine_releases_json_legacy(self):
        self.loggerich.log_status("Creating sapmachine_releases.json...")
        majors = []
        assets = OrderedDict()
        for major in utils.sapmachine_dev_releases():
            id = str(major) + "-ea"
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True})
            self.process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, True, generate_checksums=True)

        for major in utils.sapmachine_active_releases():
            id = str(major) + "-ea"
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': True})
            self.process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, True, generate_checksums=True)
            id = str(major)
            majors.append({'id': id, 'label': f"SapMachine {major}", 'lts': True if utils.sapmachine_is_lts(major) else False, 'ea': False})
            self.process_major_release(self.sm_releases[str(major)]['updates'].values(), assets, id, False, generate_checksums=True)

        json_root = {}
        json_root['majors'] = majors
        json_root['imageTypes'] = imageTypes
        json_root['assets'] = assets

        with open(join(self.output_dir, 'sapmachine_releases.json'), 'bw') as output_file:
            output_file.write(json.dumps(json_root, indent=2).encode('utf-8') + b'\n')

        self.loggerich.log("Created sapmachine_releases.json.")
        self.loggerich.clear_status()

    def write_template_file(self, filename, data):
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'bw') as output_file:
            output_file.write(data.encode('utf-8'))

    def create_latest_links(self):
        self.loggerich.log_status("Creating latest links...")
        wrote_latest = False
        for major in sorted(self.sm_releases.keys(), reverse=True):
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
                    self.write_template_file(join(self.output_dir_latest, 'latest', 'index.md'),
                                        Template(latest_overall_template).substitute(url = latest_data['url']))
                    wrote_latest = True

                self.write_template_file(join(self.output_dir_latest, 'latest', major, 'index.md'),
                                    Template(latest_overall_template).substitute(url = latest_data['url']))

                for platform, archives in latest_data['assets']['jdk'].items():
                    for archive_type, archive_data in archives.items():
                        real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
                        self.write_template_file(join(self.output_dir_latest, 'latest', major, real_platform, 'jdk', 'index.md'),
                                            Template(latest_template_download).substitute(
                                                major = major,
                                                platform = real_platform,
                                                checksum = 'sha256 ' + archive_data['checksum'],
                                                url = archive_data['url']))

                for platform, archives in latest_data['assets']['jre'].items():
                    for archive_type, archive_data in archives.items():
                        real_platform = platform + '-installer' if archive_type in ['dmg', 'msi'] else platform
                        self.write_template_file(join(self.output_dir_latest, 'latest', major, real_platform, 'jre', 'index.md'),
                                            Template(latest_template_download).substitute(
                                                major = major,
                                                platform = real_platform,
                                                checksum = 'sha256 ' + archive_data['checksum'],
                                                url = archive_data['url']))

            elif os.path.exists(join(self.output_dir_latest, 'latest', major)):
                rmtree(join(self.output_dir_latest, 'latest', major))

    def push_to_git(self):
        utils.run_cmd(['git', 'add', '.'], cwd=self.local_repo)
        _, diff, _ = utils.run_cmd("git diff HEAD".split(' '), cwd=self.local_repo, std=True)
        if not diff.strip():
            self.loggerich.log("No changes to commit.")
            return

        if self.args.tag is not None:
            commit_message = f"Update release data for release {self.args.tag}"
        elif self.args.update is not None:
            commit_message = f"Update release data for update version {self.args.update}"
        elif self.args.major is not None:
            commit_message = f"Update release data for major version {self.args.major}"
        else:
            commit_message= 'Update release data'
        utils.git_commit(self.local_repo, commit_message, '.')

        if not self.args.dry_run:
            sapMachinePushURL= str.format('https://{0}:{1}@github.com/SAP/SapMachine.git', os.environ['GIT_USER'], os.environ['GIT_PASSWORD'])
            utils.run_cmd(str.format('git push {0}', sapMachinePushURL).split(' '), cwd=self.local_repo)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', choices=['files', 'git'], default='files', help='output target, either "files" or "git". The latter means that changes are pushed to their location in SapMachine git repo, branch gh-pages. Default is "files"', metavar='OUTPUT_TARGET')
    parser.add_argument('--output-prefix', default='sapmachine-releases', help='file name prefix to generate output files containing SapMachine release information. Only used when "--output files" is set. Default is "sapmachine-releases"', metavar='OUTPUT_PREFIX')
    parser.add_argument('-i', '--input', choices=['github', 'file'], default='github', help='input source, can be either "github" or "file". Default is "github". For "file", an input file is needed that contains the results of the GitHub Release API call in json format. The default name would be "github-releases.json" and can be modified with option "--input-file"', metavar='INPUT_SOURCE')
    parser.add_argument('--github-data-file', default='github-releases.json', help='input file that contains the results of the GitHub Release API call in json format (optional). Default: "github-releases.json"', metavar='DATA_FILE')
    parser.add_argument('--store-github-data', action='store_true', help='stores queried GitHub data in DATA_FILE')
    parser.add_argument('-m', '--major', help='rebuild data for a certain major version, e.g. "21", "17"...', metavar='MAJOR')
    parser.add_argument('-u', '--update', help='rebuild data for a certain update version, e.g. "21", "17.0.3"...', metavar='UPDATE')
    parser.add_argument('-t', '--tag', help='rebuild data for a certain release/build, e.g. "sapmachine-17", "sapmachine-11.0.18", "sapmachine-22+26", ... In that case, GitHub Release information is queried only for the specified tag', metavar='TAG')
    parser.add_argument('-s', '--scratch-data', action='store_true', help='clear existing release data and rebuild everything. The default is to update existing data. Does not work in conjunction with "--tag"')
    parser.add_argument('--dry-run', action='store_true', help='no git push')
    parser.add_argument('--no-status', action='store_true', help='no git push')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode')
    args = parser.parse_args()

    if sum(1 for var in [args.major, args.update, args.tag] if var is not None) > 1:
        print(f"You can speficy at most one out of options '--major', '--update', --'tag'")
        return -1

    generator = Generator(args)

    if args.output == 'git':
        generator.setup_git()

    generator.load_sapmachine_release_data()

    generator.load_github_release_data()

    generator.iterate_releases()

    generator.generate_sapmachine_releases_json_latest()

    generator.generate_sapmachine_releases_json_website()

    generator.generate_sapmachine_releases_json_legacy()

    generator.create_latest_links()

    if args.output == 'git':
        generator.push_to_git()

    return 0

if __name__ == "__main__":
    sys.exit(main())
