'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
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
        'name': 'sapmachine-11.0.10',
        'assets': [
            {
                'name': 'sapmachine-jdk-11.0.10_linux-aarch64_bin.tar.gz',
                'browser_download_url': 'https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.10%2B9/OpenJDK11U-jdk_aarch64_linux_hotspot_11.0.10_9.tar.gz'
            }
        ]
    },
    {
        'prerelease': False,
        'name': 'sapmachine-14.0.2',
        'assets': [
            {
                'name': 'sapmachine-jdk-14.0.2_linux-aarch64_bin.tar.gz',
                'browser_download_url': 'https://github.com/AdoptOpenJDK/openjdk14-binaries/releases/download/jdk-14.0.2%2B12/OpenJDK14U-jdk_aarch64_linux_hotspot_14.0.2_12.tar.gz'
            }
        ]
    },
    {
        'prerelease': False,
        'name': 'sapmachine-16.0.2',
        'assets': [
            {
                'name': 'sapmachine-jdk-16.0.2_macos-aarch64_bin.tar.gz',
                'browser_download_url': 'https://github.com/AdoptOpenJDK/openjdk16-binaries/releases/download/jdk-16.0.1%2B9/OpenJDK16U-jdk_x64_mac_hotspot_16.0.1_9.tar.gz'
            }
        ]
    },
    {
        'prerelease': False,
        'name': 'sapmachine-15.0.2',
        'assets': [
            {
                'name': 'sapmachine-jdk-15.0.2_linux-aarch64_bin.tar.gz',
                'browser_download_url': 'https://github.com/AdoptOpenJDK/openjdk15-binaries/releases/download/jdk-15.0.2%2B7/OpenJDK15U-jdk_aarch64_linux_hotspot_15.0.2_7.tar.gz'
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
    platform = str.format('{0}-{1}_bin', utils.get_system(), utils.get_arch())
    retries = 2

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

                            if utils.get_system() == 'osx':
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
