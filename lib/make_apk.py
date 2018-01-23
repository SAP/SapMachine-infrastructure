'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import argparse
import utils

from string import Template

from os import mkdir

from os.path import join
from os.path import realpath
from os.path import exists
from os.path import expanduser

from shutil import rmtree

def generate_configuration(templates_dir, target_dir, package_name, version, package_release, description, archive_url):
    archive_name = archive_url.rsplit('/', 1)[-1]

    with open(join(templates_dir, 'APKBUILD'), 'r') as apkbuild_template:
        with open(join(target_dir, 'APKBUILD'), 'w+') as apkbuild_out:
            apkbuild_out.write(Template(apkbuild_template.read()).substitute(
                package_name=package_name,
                package_version=version.replace('+', '.'),
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
    cwd = os.getcwd()
    home = expanduser("~")
    work_dir = join(cwd, 'apk_work')
    version, major, build_number, sap_build_number = utils.sapmachine_tag_components(tag)
    jdk_url, jre_url = utils.fetch_tag(tag, 'linux-x64-musl', utils.get_github_api_accesstoken())
    jdk_name = str.format('sapmachine-{0}-jdk', major)
    jre_name = str.format('sapmachine-{0}-jre', major)
    jdk_dir = join(work_dir, jdk_name)
    jre_dir = join(work_dir, jre_name)

    if exists(work_dir):
        rmtree(work_dir)

    mkdir(work_dir)
    mkdir(jdk_dir)
    mkdir(jre_dir)

    generate_configuration(templates_dir, jdk_dir, jdk_name, version, '0', 'The SapMachine Java Development Kit', jdk_url)
    generate_configuration(templates_dir, jre_dir, jre_name, version, '0', 'The SapMachine Java Runtime Environment', jre_url)

    utils.run_cmd(['abuild', 'checksum'], cwd=jdk_dir)
    utils.run_cmd(['abuild', 'checksum'], cwd=jre_dir)

    utils.run_cmd(['abuild', '-r'], cwd=jdk_dir)
    utils.run_cmd(['abuild', '-r'], cwd=jre_dir)

    rmtree(work_dir)

    utils.make_tgz_archive(join(home, 'packages'), join(cwd, 'packages.tar.gz'))

if __name__ == "__main__":
    sys.exit(main())