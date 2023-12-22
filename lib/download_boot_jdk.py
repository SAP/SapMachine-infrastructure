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

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--major', help='the SapMachine major version to build', metavar='MAJOR')
    parser.add_argument('-d', '--destination', help='the download destination', metavar='DIR')
    args = parser.parse_args()

    if args.major is not None:
        major = int(args.major)
    else:
        version_input = []
        if 'SAPMACHINE_VERSION' in os.environ:
            version_input.append(os.environ['SAPMACHINE_VERSION'])
        if 'GIT_REF' in os.environ:
            version_input.append(os.environ['GIT_REF'])
        major = utils.calc_major(filter(None, version_input))
        if major is None:
            print("Could not detect major version")
            return -1

    destination = os.path.realpath(os.getcwd() if args.destination is None else args.destination)
    boot_jdk_exploded = join(destination, 'boot_jdk')
    boot_jdk_infofile = join(destination, "bootstrapjdk.txt")
    current_boot_jdk = None
    if os.path.exists(boot_jdk_infofile):
        with open(boot_jdk_infofile, "r") as file:
            current_boot_jdk = file.read()
            print(f"Current Boot JDK: {current_boot_jdk}")

    system = utils.get_system()
    platform = f"{system}-{utils.get_arch()}{'-musl' if os.path.isfile('/etc/alpine-release') else ''}"
    print(f"Detected platform: {platform}")

    # Look for latest GA build. If none available, get latest EA build.
    ga = False
    asset_name = None
    asset_url = None
    for l_major in map(str, range(major, major - 3, -1)):
        sapmachine_releases = utils.get_sapmachine_releases(l_major)
        if not l_major in sapmachine_releases:
            continue

        if not 'updates' in sapmachine_releases[l_major]:
            continue

        for d_updates in sapmachine_releases[l_major].values():
            if not isinstance(d_updates, dict):
                continue
            for d_builds in d_updates.values():
                for d_build in d_builds.values():
                    if asset_name is not None and d_build['ea'] == 'true':
                        continue
                    if 'assets' not in d_build or 'jdk' not in d_build['assets'] or platform not in d_build['assets']['jdk']:
                        continue
                    for archive_type in d_build['assets']['jdk'][platform]:
                        if archive_type in ['tar.gz', 'zip']:
                            asset_name = d_build['assets']['jdk'][platform][archive_type]['name']
                            asset_url = d_build['assets']['jdk'][platform][archive_type]['url']
                            break
                    if d_build['ea'] == 'false':
                        ga = True
                        break
                if ga: break
            if ga: break
        if ga: break

    # return if we can't find a suitable Boot JDK
    if asset_name is None:
        print("Could not find a suitable Boot JDK.")
        return -1

    print(f"Identified Boot JDK {asset_name}, url: {asset_url}")

    if current_boot_jdk is not None and current_boot_jdk == asset_name and os.path.exists(boot_jdk_exploded):
        print(f"Boot JDK {current_boot_jdk} already downloaded.")
        return 0

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

    with open(boot_jdk_infofile, "w") as file:
        file.write(asset_name)

if __name__ == "__main__":
    sys.exit(main())
