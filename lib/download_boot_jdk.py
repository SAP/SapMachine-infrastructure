'''
Copyright (c) 2019-2023 by SAP SE, Walldorf, Germany.
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

# This list is a temporary solution for platforms that we have not yet delivered with SapMachine
# Currently: AIX
extra_bootjdks = [
    {
        'prerelease': False,
        'name': 'sapmachine-21',
        'assets': [
            {
                'name': 'sapmachine-jdk-21_aix-ppc64_bin.tar.gz',
                'browser_download_url': 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.1%2B1/sapmachine-jdk-21.0.1-eabeta.1_aix-ppc64_bin.tar.gz'
            }
        ]
    }
]

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--major', help='the SapMachine major version to build', metavar='MAJOR')
    parser.add_argument('-d', '--destination', help='the download destination', metavar='DIR')
    args = parser.parse_args()

    version_input = []
    if 'SAPMACHINE_VERSION' in os.environ:
        version_input.append(os.environ['SAPMACHINE_VERSION'])
    if 'GIT_REF' in os.environ:
        version_input.append(os.environ['GIT_REF'])
    boot_jdk_major_max = utils.calc_major(filter(None, version_input)) if args.major is None else int(args.major)
    if boot_jdk_major_max is None:
        print("Could not detect major version")
        return -1

    boot_jdk_major_min = boot_jdk_major_max - 1
    destination = os.path.realpath(os.getcwd() if args.destination is None else args.destination)
    boot_jdk_exploded = join(destination, 'boot_jdk')
    boot_jdk_infofile = join(destination, "bootstrapjdk.txt")
    current_boot_jdk = None
    if os.path.exists(boot_jdk_infofile):
        with open(boot_jdk_infofile, "r") as file:
            current_boot_jdk = file.read()
            print(str.format("Current Boot JDK: {0}", current_boot_jdk))

    releases = utils.get_github_releases()
    system = utils.get_system()
    platform = str.format('{0}-{1}{2}_bin', system, utils.get_arch(), "-musl" if os.path.isfile('/etc/alpine-release') else "")
    print(str.format('detected platform "{0}"', platform))

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
                        if current_boot_jdk is not None and current_boot_jdk == asset_name and os.path.exists(boot_jdk_exploded):
                            print(str.format("Boot JDK {0} already downloaded.", current_boot_jdk))
                            return 0
                        with open(boot_jdk_infofile, "w") as file:
                            file.write(asset_name)
                        archive_path = join(destination, asset_name)
                        utils.remove_if_exists(archive_path)
                        utils.download_artifact(asset_url, archive_path)
                        utils.remove_if_exists(boot_jdk_exploded)
                        os.makedirs(boot_jdk_exploded)
                        utils.extract_archive(archive_path, boot_jdk_exploded, remove_archive=True)

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

    # if we return here, we couldn't download a suitable Boot JDK
    print("Returning without finding suitable Boot JDK.")
    return -1

if __name__ == "__main__":
    sys.exit(main())
