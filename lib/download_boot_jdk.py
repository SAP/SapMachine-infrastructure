'''
Copyright (c) 2019-2021 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import glob
import os
import shutil
import sys
import utils

from os.path import join
from versions import SapMachineTag

# this list is a temporary solution until we have aarch64 release available
# remove this list once they are available
extra_bootjdks = [
    {
        'prerelease': False,
        'name': 'sapmachine-11.0.12',
        'assets': [
            {
                'name': 'sapmachine-jdk-11.0.12_linux-aarch64_bin.tar.gz',
                'browser_download_url': 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.12/sapmachine-jdk-11.0.12-beta_linux-aarch64_bin.tar.gz'
            }
        ]
    },
    {
        'prerelease': False,
        'name': 'sapmachine-16.0.2',
        'assets': [
            {
                'name': 'sapmachine-jdk-16.0.2_linux-aarch64_bin.tar.gz',
                'browser_download_url': 'https://github.com/SAP/SapMachine/releases/download/sapmachine-16.0.2/sapmachine-jdk-16.0.2-beta_linux-aarch64_bin.tar.gz'
            }
        ]
    },
    {
        'prerelease': False,
        'name': 'sapmachine-17',
        'assets': [
            {
                'name': 'sapmachine-jdk-17_linux-aarch64_bin.tar.gz',
                'browser_download_url': 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17/sapmachine-jdk-17-beta_linux-aarch64_bin.tar.gz'
            }
        ]
    }
]

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--major', help='the SapMachine major version to build', metavar='MAJOR', required=True)
    parser.add_argument('-d', '--destination', help='the download destination', metavar='DIR', required=True)
    args = parser.parse_args()

    boot_jdk_major_max = int(args.major)
    boot_jdk_major_min = boot_jdk_major_max - 1
    destination = os.path.realpath(args.destination)
    releases = utils.get_github_releases()
    system = utils.get_system(boot_jdk_major_max)
    platform = str.format('{0}-{1}_bin', system, utils.get_arch())
    retries = 2

    print(str.format('detected platform "{0}"', platform))

    releases = extra_bootjdks + releases

    while retries > 0:
        for release in releases:

            if release['prerelease']:
                continue

            tag = SapMachineTag.from_string(release['name'])

            if tag is None:
                print(str.format("SapMachine release {0} not recognized", release['name']))
                continue
            major = tag.get_major()

            if major <= boot_jdk_major_max and major >= boot_jdk_major_min:
                assets = release['assets']

                for asset in assets:
                    asset_name = asset['name']
                    asset_url = asset['browser_download_url']

                    if 'jdk' in asset_name and platform in asset_name and (asset_name.endswith('.tar.gz') or asset_name.endswith('.zip')) and 'symbols' not in asset_name:
                        archive_path = join(destination, asset_name)
                        utils.remove_if_exists(archive_path)
                        utils.download_artifact(asset_url, archive_path)
                        boot_jdk_exploded = join(destination, 'boot_jdk')
                        utils.remove_if_exists(boot_jdk_exploded)
                        os.makedirs(boot_jdk_exploded)
                        utils.extract_archive(archive_path, boot_jdk_exploded)

                        sapmachine_folder = [f for f_ in [glob.glob(join(boot_jdk_exploded, e)) for e in ('sapmachine*', 'jdk*')] for f in f_]

                        if sapmachine_folder is not None:
                            sapmachine_folder = sapmachine_folder[0]
                            files = os.listdir(sapmachine_folder)

                            for f in files:
                                shutil.move(join(sapmachine_folder, f), boot_jdk_exploded)

                            utils.remove_if_exists(sapmachine_folder)

                            if system == 'osx' or system == 'macos':
                                files = os.listdir(join(boot_jdk_exploded, 'Contents', 'Home'))

                                for f in files:
                                    shutil.move(join(boot_jdk_exploded, 'Contents', 'Home', f), boot_jdk_exploded)

                                utils.remove_if_exists(join(boot_jdk_exploded, 'Contents'))

                        return 0
        retries -= 1
        if retries == 1:
            boot_jdk_major_min = boot_jdk_major_max - 2

    return 0

if __name__ == "__main__":
    sys.exit(main())
