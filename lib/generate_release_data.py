'''
Copyright (c) 2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import json
import os
import re
import sys
import utils

from urllib.error import HTTPError
from urllib.request import urlopen, Request
from utils import github_api_request
from utils import sapmachine_is_lts
from versions import SapMachineTag

tags = None
number_of_releases = 0
release_count = 0
asset_name = None
last_len = 0

def log_status(text = None):
    global tags, number_of_releases, release_count, asset_name, last_len

    if tags is None:
        status_text = f"Processing..."
    elif asset_name is None:
        status_text = f"Processing release {tags} ({release_count}/{number_of_releases})..."
    else:
        status_text = f"Processing release {tags} ({release_count}/{number_of_releases}): {asset_name}..."

    if text is None:
        new_len = len(status_text)
        status_text = status_text.ljust(last_len)
        last_len = new_len
    else:
        text.rjust(last_len)
        last_len = len(status_text)
        print(text)

    print(status_text, end='\r')

def main(argv=None):
    global tags, number_of_releases, release_count, asset_name, last_len

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_file', default='all-releases.json', help='Ouput file containing SapMachine releases', metavar='INPUT_FILE')
    parser.add_argument('-i', '--input_file', help='Provide an input file that contains the results of the GitHub Release API call as json', metavar='OUTPUT_FILE')
    parser.add_argument('-s', '--scratch', action='store_true', help='Ignore output file if it already exists. The default is to update an existing file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    args = parser.parse_args()

    # Load existing data file or scratch
    if args.scratch or not os.path.exists(args.output_file):
        print(f"Creating release data file {args.output_file}.", end='')
        sm_releases = {}
    else:
        print(f"Updating release data file {args.output_file}.", end='')
        with open(args.output_file, 'r') as file:
            sm_releases = json.load(file)

    # Load input data from GitHub or file
    if args.input_file is None:
        print(" Source: GitHub.")
        gh_releases = github_api_request('releases', per_page=300)
    else:
        print(f" Source: {args.input_file}.")
        with open(args.input_file, 'r') as file:
            gh_releases = json.load(file)

    # Loop through releases
    number_of_releases = len(gh_releases)
    release_count = 1
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    checksum_pattern = re.compile(utils.sapmachine_checksum_pattern())
    for release in gh_releases:
        tags = release['tag_name']
        if tags is None:
            log_status(f"Release {release['html_url']} does not have a tag, skipping.")
            release_count += 1
            continue
        log_status()

        if not 'assets' in release or not isinstance(release['assets'], list) :
            log_status(f"Release {tags} has no assets, skipping.")
            release_count += 1
            continue

        tag = SapMachineTag.from_string(tags)
        major = str(tag.get_major())

        d_major = sm_releases.get(major, None)
        if d_major is None:
            d_major = {}
            d_major['lts'] = str(sapmachine_is_lts(major)).lower()
            sm_releases[major] = d_major

        d_updates = d_major.get('updates', None)
        if d_updates is None:
            d_updates = {}
            d_major['updates'] = d_updates

        update = tag.get_version_string_without_build()
        d_update = d_updates.get(update, None)
        if d_update is None:
            d_update = {}
            d_updates[update] = d_update

        d_build = d_update.get(tags, None)
        if d_build is None:
            d_build = {}
            d_update[tags] = d_build

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
            asset_name = asset['name']
            log_status()

            is_asset = False
            match = asset_pattern.match(asset_name)
            checksum_match = checksum_pattern.match(asset_name)
            if match is not None:
                image_type = match.group(1)
                platform = match.group(3)
                is_asset = True
            elif checksum_match is not None:
                image_type = checksum_match.group(1)
                platform = checksum_match.group(3)
            elif 'symbols' in asset_name:
                if args.verbose:
                    log_status(f"Skipped {asset_name} because it is a symbol archive or checksum.")
                continue
            elif 'rpm' in asset_name:
                if args.verbose:
                    log_status(f"Skipped {asset_name} because it is an rpm archive or checksum.")
                continue
            else:
                log_status(f"Skipped {asset_name} because it is no viable archive or checksum.")
                continue

            if platform == 'osx-x64':
                platform = 'macos-x64'

            if platform == 'osx-aarch64':
                platform = 'macos-aarch64'

            if is_asset:
                if args.verbose:
                    log_status(f"{asset_name} is an archive file for {platform}.")
            else:
                if asset_name.endswith('dmg.sha256.txt') or asset_name.endswith('msi.sha256.txt'):
                    asset_name = asset_name[:-len('.sha256.txt')]
                elif asset_name.endswith('sha256.txt'):
                    asset_name = asset_name[:-len('.sha256.txt')] + ('.zip' if platform == 'windows-x64' else '.tar.gz')

            d_type = d_jdks if image_type == 'jdk' else d_jres if image_type == 'jre' else None
            if d_type is None:
                log_status(f"Image Type {image_type} is unknown.")
                continue

            if platform in d_type.keys():
                d_platform = d_type[platform]
            else:
                d_platform = {}
                d_type[platform] = d_platform

            if asset_name.endswith('tar.gz'):
                asset_type = 'tar.gz'
            elif asset_name.endswith('zip'):
                asset_type = 'zip'
            elif asset_name.endswith('msi'):
                asset_type = 'msi'
            elif asset_name.endswith('dmg'):
                asset_type = 'dmg'
            else:
                log_status(f"{asset_name} is an unsupported asset type.")
                continue

            if asset_type in d_platform:
                d_asset = d_platform[asset_type]
            else:
                d_asset = {}
                d_platform[asset_type] = d_asset

            if 'name' in d_asset:
                if d_asset['name'] != asset_name:
                    log_status(f"{asset_name} does not match existing name {d_asset['name']}.")
                    break
            else:
                d_asset['name'] = asset_name

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
                        if args.verbose:
                            log_status(f"Downloaded checksum for {asset_name}: {checksum}")

                        d_asset['checksum'] = checksum

                    except HTTPError as httpError:
                        log_status(f"Checksum file for {asset_name} could not be downloaded from {asset['browser_download_url']}: {httpError.code} ({httpError.reason})")

        if not d_jdks:
            del d_assets['jdk']
        if not d_jres:
            del d_assets['jre']

        # Save data to file
        with open(args.output_file, 'w') as output_file:
            json.dump(sm_releases, output_file, indent=2)

        release_count += 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
