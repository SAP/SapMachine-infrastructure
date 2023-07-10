'''
Copyright (c) 2017-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import codecs
import datetime
import glob
import os
import re
import sys
import utils

from os import mkdir
from os import listdir
from os.path import join
from os.path import realpath
from os.path import basename
from os.path import isfile
from shutil import move
from string import Template
from versions import SapMachineTag

def generate_package_string(package_fmt, major):
    tokens = []
    tokens.append(str.format(package_fmt, 2))
    for i in range(5, int(major) + 1):
        tokens.append(str.format(package_fmt, i))
    return ", ".join(tokens)

def gather_licenses(src_dir):
    licenses = []
    separator = '------------------------------------------------------------------------------'

    license_files = [
        join(src_dir, 'LICENSE'),
        join(src_dir, 'ASSEMBLY_EXCEPTION')
    ]

    for root, dirs, files in os.walk(join(src_dir, 'src'), topdown=False):
        if root.endswith('legal'):
            for entry in files:
                license_files.append(join(root, entry))

    for license_file in license_files:
        with codecs.open(license_file, 'r', 'utf-8') as f:
            content = f.read()
            content = content.replace('<pre>', '').replace('</pre>', '')
            licenses.append(content)
            licenses.append(separator)

    return '\n'.join([license for license in licenses])

def generate_configuration(templates_dir, major, arch, target_dir, exploded_image, src_dir, download_url, package_fmt, headless = False):
    bin_dir = join(exploded_image, 'bin')
    tools = [f for f in listdir(bin_dir) if isfile(join(bin_dir, f))]
    now = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    provides_packages = generate_package_string(package_fmt, major)

    with open(join(templates_dir, 'control'), 'r') as control_template:
        with open(join(target_dir, 'control'), 'w+') as control_out:
            control_out.write(Template(control_template.read()).substitute(major=major, arch=arch, provides_packages=provides_packages))

    with open(join(templates_dir, '..', 'install'), 'r') as install_template:
        with open(join(target_dir, 'install'), 'w+') as install_out:
            install_out.write(Template(install_template.read()).substitute(exploded_image=basename(exploded_image), major=major))

    with open(join(templates_dir, '..', 'postinst'), 'r') as postinst_template:
        with open(join(target_dir, 'postinst'), 'w+') as postinst_out:
            postinst_out.write(Template(postinst_template.read()).substitute(tools=' '.join([tool for tool in tools]), major=major))

    with open(join(templates_dir, '..', 'copyright'), 'r') as copyright_template:
        with codecs.open(join(target_dir, 'copyright'), 'w+', 'utf-8') as copyright_out:
            template = Template(copyright_template.read())
            copyright_out.write(template.substitute(
                date_and_time=now,
                download_url=download_url,
                license=gather_licenses(src_dir)
            ))

    with open(join(target_dir, 'compat'), 'w+') as compat_out:
        compat_out.write('10')

    if headless:
        # we need to add --ignore-missing-info to the dh_shlibdeps call, otherwise we see errors on ppc64le
        with open(join(target_dir, "rules"), "a") as rulesfile:
            rulesfile.write("\noverride_dh_shlibdeps:\n\tdh_shlibdeps -Xawt -Xsplash --dpkg-shlibdeps-params=--ignore-missing-info\n")
    else:
        # we need to add --ignore-missing-info to the dh_shlibdeps call, otherwise we see errors on ppc64le
        with open(join(target_dir, "rules"), "a") as rulesfile:
            rulesfile.write("\noverride_dh_shlibdeps:\n\tdh_shlibdeps --dpkg-shlibdeps-params=--ignore-missing-info\n")

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='SapMachine version tag to create the debian package for', metavar='TAG')
    parser.add_argument('-d', '--download', help='Download artifact and clone git repo', action='store_true')
    parser.add_argument('-a', '--architecture', help='specifies the architecture (linux-aarch64, linux-ppc64le, linux-x64)', metavar='ARCH', default='linux-x64')
    args = parser.parse_args()

    cwd = os.getcwd()
    work_dir = join(cwd, 'deb_work')
    utils.remove_if_exists(work_dir)
    mkdir(work_dir)

    if not args.download:
        bundle_name_file = join(cwd, 'jre_bundle_name.txt')
        if not isfile(bundle_name_file):
            print(str.format("Bundle name file \"{0}\" does not exist. I don't know what to package", bundle_name_file))
            return -1
        with open(bundle_name_file, 'r') as file:
            jre_bundle_name = file.read().rstrip()
        print(str.format("JRE bundle name: {0}", jre_bundle_name))
        bundle_name_file = join(cwd, 'jdk_bundle_name.txt')
        if not isfile(bundle_name_file):
            print(str.format("Bundle name file \"{0}\" does not exist. I don't know what to package", bundle_name_file))
            return -1
        with open(bundle_name_file, 'r') as file:
            jdk_bundle_name = file.read().rstrip()
        print(str.format("JDK bundle name: {0}", jdk_bundle_name))

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        if args.download:
            print(str.format("Passed tag \"{0}\" is invalid. I don't know what to download!", args.tag))
            return -1
        else:
            bundle_name_match = re.compile('sapmachine-\w+-((\d+)(\.\d+)*).*').match(jdk_bundle_name)
            major = bundle_name_match.group(2)
            version = bundle_name_match.group(1).replace('-', '.')
            jre_url = "https://sapmachine.io"
            jdk_url = "https://sapmachine.io"
    else:
        major = tag.get_major()
        version = tag.get_version_string().replace('-', '.')
        if args.download:
            asset_urls = utils.get_asset_urls(tag, args.architecture)
            jre_url = asset_urls['jre']
            jdk_url = asset_urls['jdk']
        else:
            jre_url = "https://github.com/SAP/SapMachine/releases/download/sapmachine-" + tag.get_version_string() + "/" + jre_bundle_name
            jdk_url = "https://github.com/SAP/SapMachine/releases/download/sapmachine-" + tag.get_version_string() + "/" + jdk_bundle_name

    jre_headless_name = str.format('sapmachine-{0}-jre-headless-{1}', major, version)
    jre_name = str.format('sapmachine-{0}-jre-{1}', major, version)
    jdk_headless_name = str.format('sapmachine-{0}-jdk-headless-{1}', major, version)
    jdk_name = str.format('sapmachine-{0}-jdk-{1}', major, version)

    if args.download:
        src_dir = join(work_dir, 'sapmachine_master')
        utils.git_get('github.com/SAP/SapMachine', args.tag, src_dir)
        jre_archive = join(work_dir, jre_url.rsplit('/', 1)[-1])
        utils.download_artifact(jre_url, jre_archive)
        jdk_archive = join(work_dir, jdk_url.rsplit('/', 1)[-1])
        utils.download_artifact(jdk_url, jdk_archive)
    else:
        src_dir = join(cwd, 'SapMachine')
        jre_archive = join(cwd, jre_bundle_name)
        jdk_archive = join(cwd, jdk_bundle_name)

    jre_headless_dir = join(work_dir, jre_headless_name)
    mkdir(jre_headless_dir)
    utils.extract_archive(jre_archive, jre_headless_dir)
    jre_dir = join(work_dir, jre_name)
    mkdir(jre_dir)
    utils.extract_archive(jre_archive, jre_dir)
    jdk_headless_dir = join(work_dir, jdk_headless_name)
    mkdir(jdk_headless_dir)
    utils.extract_archive(jdk_archive, jdk_headless_dir)
    jdk_dir = join(work_dir, jdk_name)
    mkdir(jdk_dir)
    utils.extract_archive(jdk_archive, jdk_dir)

    env = os.environ.copy()
    env['DEBFULLNAME'] = 'SapMachine'
    env['DEBEMAIL'] = 'sapmachine@sap.com'
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jre_headless_dir, env=env)
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jre_dir, env=env)
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jdk_headless_dir, env=env)
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jdk_dir, env=env)

    jre_headless_exploded_image = glob.glob(join(jre_dir, 'sapmachine-*'))[0]
    jre_exploded_image = glob.glob(join(jre_dir, 'sapmachine-*'))[0]
    jdk_headless_exploded_image = glob.glob(join(jdk_dir, 'sapmachine-*'))[0]
    jdk_exploded_image = glob.glob(join(jdk_dir, 'sapmachine-*'))[0]

    generate_configuration(
        templates_dir = join(realpath("SapMachine-infrastructure/debian-templates"), 'jre-headless'),
        major = str(major),
        arch = "arm64" if args.architecture == "linux-aarch64" else ("ppc64el" if args.architecture == "linux-ppc64le" else "amd64"),
        target_dir = join(jre_headless_dir, 'debian'),
        exploded_image = jre_headless_exploded_image,
        src_dir = src_dir,
        download_url = jre_url,
        package_fmt = "java{0}-runtime-headless",
        headless = True)

    generate_configuration(
        templates_dir = join(realpath("SapMachine-infrastructure/debian-templates"), 'jre'),
        major = str(major),
        arch = "arm64" if args.architecture == "linux-aarch64" else ("ppc64el" if args.architecture == "linux-ppc64le" else "amd64"),
        target_dir = join(jre_dir, 'debian'),
        exploded_image = jre_exploded_image,
        src_dir = src_dir,
        download_url = jre_url,
        package_fmt = "java{0}-runtime")

    generate_configuration(
        templates_dir = join(realpath("SapMachine-infrastructure/debian-templates"), 'jdk-headless'),
        major = str(major),
        arch = "arm64" if args.architecture == "linux-aarch64" else ("ppc64el" if args.architecture == "linux-ppc64le" else "amd64"),
        target_dir = join(jdk_headless_dir, 'debian'),
        exploded_image = jdk_headless_exploded_image,
        src_dir = src_dir,
        download_url = jdk_url,
        package_fmt = "java{0}-sdk-headless",
        headless = True)

    generate_configuration(
        templates_dir = join(realpath("SapMachine-infrastructure/debian-templates"), 'jdk'),
        major = str(major),
        arch = "arm64" if args.architecture == "linux-aarch64" else ("ppc64el" if args.architecture == "linux-ppc64le" else "amd64"),
        target_dir = join(jdk_dir, 'debian'),
        exploded_image = jdk_exploded_image,
        src_dir = src_dir,
        download_url = jdk_url,
        package_fmt = "java{0}-sdk")

    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jre_headless_dir, env=env)
    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jre_dir, env=env)
    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jdk_headless_dir, env=env)
    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jdk_dir, env=env)

    deb_files = glob.glob(join(work_dir, '*.deb'))

    for deb_file in deb_files:
        move(deb_file, cwd)

    return 0

if __name__ == "__main__":
    sys.exit(main())
