'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import argparse
import glob
import utils

from string import Template

from os import mkdir

from os.path import join
from os.path import realpath
from os.path import exists
from os.path import expanduser

from shutil import rmtree
from shutil import copytree
from shutil import move
from shutil import copy

def generate_configuration(templates_dir, target_dir, package_name, version, package_release, description, archive_url):
    archive_name = archive_url.rsplit('/', 1)[-1]

    with open(join(templates_dir, 'APKBUILD'), 'r') as apkbuild_template:
        with open(join(target_dir, 'APKBUILD'), 'w+') as apkbuild_out:
            apkbuild_out.write(Template(apkbuild_template.read()).substitute(
                package_name=package_name,
                package_version=version.replace('+', '.').replace('-', '.'),
                package_release=package_release,
                package_description=description,
                archive_url=archive_url,
                archive_name=archive_name))

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the tag to create the alpine packages from', metavar='TAG', required=True)
    parser.add_argument('-d', '--templates-directory', help='specify the templates directory', metavar='DIR', required=True)
    args = parser.parse_args()

    templates_dir = realpath(args.templates_directory)
    tag = args.tag

    if tag.endswith('-alpine'):
        # the "-alpine" tags do not contain any assets
        tag = tag[:-len('-alpine')]

    cwd = os.getcwd()
    home = expanduser("~")
    work_dir = join(cwd, 'apk_work')
    version, version_part, major, update, version_sap, build_number, os_ext = utils.sapmachine_tag_components(tag)
    jdk_url, jre_url = utils.get_asset_url(tag, 'linux-x64-musl')
    jdk_name = str.format('sapmachine-{0}-jdk', major)
    jre_name = str.format('sapmachine-{0}-jre', major)
    jdk_dir = join(work_dir, jdk_name)
    jre_dir = join(work_dir, jre_name)

    utils.remove_if_exists(work_dir)

    mkdir(work_dir)
    mkdir(jdk_dir)
    mkdir(jre_dir)

    generate_configuration(templates_dir, jdk_dir, jdk_name, version, '0', 'The SapMachine Java Development Kit', jdk_url)
    generate_configuration(templates_dir, jre_dir, jre_name, version, '0', 'The SapMachine Java Runtime Environment', jre_url)

    utils.run_cmd(['abuild', 'checksum'], cwd=jdk_dir)
    utils.run_cmd(['abuild', 'checksum'], cwd=jre_dir)

    utils.run_cmd(['abuild', '-r', '-K'], cwd=jdk_dir)
    utils.run_cmd(['abuild', '-r', '-K'], cwd=jre_dir)

    rmtree(work_dir)

    apk_files = glob.glob(join(home, 'packages', 'apk_work','*', '*.apk'))

    for apk_file in apk_files:
        copy(apk_file, cwd)

if __name__ == "__main__":
    sys.exit(main())