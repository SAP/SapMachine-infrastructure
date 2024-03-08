'''
Copyright (c) 2017-2024 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import glob
import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import utils

from os import mkdir
from os.path import expanduser
from os.path import join
from os.path import realpath
from os.path import isfile
from shutil import copy
from shutil import rmtree
from string import Template
from versions import SapMachineTag

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

    with open(join(target_dir, 'APKBUILD'), 'r') as file:
        print('APKBUILD content:')
        print(file.read())

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the tag to create the alpine packages from', metavar='TAG', required=True)
    parser.add_argument('-d', '--download', help='Download artifact and clone git repo', action='store_true')
    parser.add_argument('--templates-directory', help='specify the templates directory', metavar='DIR', required=True)
    args = parser.parse_args()

    cwd = os.getcwd()
    work_dir = join(cwd, 'apk_work')
    print("work_dir:", work_dir)
    utils.remove_if_exists(work_dir)
    mkdir(work_dir)

    if not args.download:
        bundle_name_file = join(cwd, 'jre_bundle_name.txt')
        if not isfile(bundle_name_file):
            print(f"Bundle name file \"{bundle_name_file}\" does not exist. I don't know what to package")
            return -1
        with open(bundle_name_file, 'r') as file:
            jre_bundle_name = file.read().rstrip()
        print(f"JRE bundle name: {jre_bundle_name}")
        bundle_name_file = join(cwd, 'jdk_bundle_name.txt')
        if not isfile(bundle_name_file):
            print(f"Bundle name file \"{bundle_name_file}\" does not exist. I don't know what to package")
            return -1
        with open(bundle_name_file, 'r') as file:
            jdk_bundle_name = file.read().rstrip()
        print(f"JDK bundle name: {jdk_bundle_name}")

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        if args.download:
            print(f"Passed tag \"{args.tag}\" is invalid. I don't know what to download!")
            return -1
        else:
            bundle_name_match = re.compile('sapmachine-\w+-((\d+)(\.\d+)*).*').match(jdk_bundle_name)
            major = bundle_name_match.group(2)
    else:
        major = tag.get_major()
        if args.download:
            urls = utils.get_asset_urls(tag, 'linux-x64-musl')
            jre_source = urls['jre']
            jdk_source = urls['jdk']
        else:
            jre_source = cwd + "/" + jre_bundle_name
            jdk_source = cwd + "/" + jdk_bundle_name

    templates_dir = realpath(args.templates_directory)

    jre_name = f'sapmachine-{major}-jre'
    jdk_name = f'sapmachine-{major}-jdk'
    jre_dir = join(work_dir, jre_name)
    jdk_dir = join(work_dir, jdk_name)

    mkdir(jre_dir)
    mkdir(jdk_dir)

    print(f"JRE dir: {jre_dir}")
    copy(jre_bundle_name, jre_dir + '/' + jre_bundle_name)
    generate_configuration(templates_dir, jre_dir, jre_name, tag.get_version_string(), '0', 'The SapMachine Java Runtime Environment', jre_bundle_name)
    print(f"JDK dir: {jdk_dir}")
    copy(jdk_bundle_name, jdk_dir + '/' + jdk_bundle_name)
    generate_configuration(templates_dir, jdk_dir, jdk_name, tag.get_version_string(), '0', 'The SapMachine Java Development Kit', jdk_bundle_name)

    utils.run_cmd(['abuild', 'checksum'], cwd=jre_dir)
    utils.run_cmd(['abuild', 'checksum'], cwd=jdk_dir)

    utils.run_cmd(['abuild', '-r', '-K'], cwd=jre_dir)
    utils.run_cmd(['abuild', '-r', '-K'], cwd=jdk_dir)

    rmtree(work_dir)

    apk_files = glob.glob(join(expanduser("~"), 'packages', 'apk_work', '*', '*.apk'))

    for apk_file in apk_files:
        copy(apk_file, cwd)

    return 0

if __name__ == "__main__":
    sys.exit(main())
