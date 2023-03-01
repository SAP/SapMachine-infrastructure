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

from os import remove
from os import mkdir
from os import listdir
from os.path import join
from os.path import realpath
from os.path import basename
from os.path import isfile
from shutil import copy
from string import Template
from versions import SapMachineTag

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

def generate_configuration(templates_dir, major, arch, target_dir, exploded_image, src_dir, download_url):
    bin_dir = join(exploded_image, 'bin')
    tools = [f for f in listdir(bin_dir) if isfile(join(bin_dir, f))]
    now = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

    with open(join(templates_dir, 'control'), 'r') as control_template:
        with open(join(target_dir, 'control'), 'w+') as control_out:
            control_out.write(Template(control_template.read()).substitute(major=major, arch=arch))

    with open(join(templates_dir, 'install'), 'r') as install_template:
        with open(join(target_dir, 'install'), 'w+') as install_out:
            install_out.write(Template(install_template.read()).substitute(exploded_image=basename(exploded_image), major=major))

    with open(join(templates_dir, 'postinst'), 'r') as postinst_template:
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

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='SapMachine version tag to create the debian package for', metavar='TAG')
    parser.add_argument('-d', '--download', help='Download artifact and clone git repo', action='store_true')
    parser.add_argument('-a', '--architecture', help='specifies the architecture (linux-aarch64, linux-ppc64le, linux-x64)', metavar='ARCH', default='linux-x64')
    parser.add_argument('-y', '--type', help='specifies whether a jdk (default) or a jre should be build (jdk, jre)', metavar='TYPE', default='jdk')
    args = parser.parse_args()

    cwd = os.getcwd()
    work_dir = join(cwd, 'deb_work')
    utils.remove_if_exists(work_dir)
    mkdir(work_dir)
    t=args.type

    if not args.download:
        bundle_name_file = join(cwd, t, '_bundle_name.txt')
        if not isfile(bundle_name_file):
            print(str.format("Bundle name file \"{0}\" does not exist. I don't know what to package", bundle_name_file))
            return -1
        with open(bundle_name_file, 'r') as file:
            bundle_name = file.read().rstrip()
        print(str.format("Bundle Name: {0}", bundle_name))

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        if args.download:
            print(str.format("Passed tag \"{0}\" is invalid. I don't know what to download!", args.tag))
            return -1
        else:
            bundle_name_match = re.compile('sapmachine-\w+-((\d+)(\.\d+)*).*').match(bundle_name)
            major = bundle_name_match.group(2)
            j_name = str.format('sapmachine-{0}-{1}-{2}', major, t, bundle_name_match.group(1).replace('-', '.'))
            j_url = "https://sapmachine.io"
    else:
        major = tag.get_major()
        j_name = str.format('sapmachine-{0}-{1}-{2}', major, t, tag.get_version_string().replace('-', '.'))
        if args.download:
            j_url = utils.get_asset_urls(tag, args.architecture, [t])[t]
        else:
            j_url = "https://github.com/SAP/SapMachine/releases/download/sapmachine-" + tag.get_version_string() + "/" + bundle_name

    if args.download:
        src_dir = join(work_dir, 'sapmachine_master')
        utils.git_clone('github.com/SAP/SapMachine', args.tag, src_dir)
        j_archive = join(work_dir, j_url.rsplit('/', 1)[-1])
        utils.download_artifact(j_url, j_archive)
    else:
        src_dir = join(cwd, 'SapMachine')
        j_archive = join(cwd, bundle_name)

    j_dir = join(work_dir, j_name)
    mkdir(j_dir)
    utils.extract_archive(j_archive, j_dir)

    env = os.environ.copy()
    env['DEBFULLNAME'] = 'SapMachine'
    env['DEBEMAIL'] = 'sapmachine@sap.com'
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=j_dir, env=env)

    j_exploded_image = glob.glob(join(j_dir, 'sapmachine-*'))[0]

    generate_configuration(
        templates_dir = join(realpath("SapMachine-Infrastructure/debian-templates"), t),
        major = str(major),
        arch = "arm64" if args.architecture == "linux-aarch64" else ("ppc64el" if args.architecture == "linux-ppc64le" else "amd64"),
        target_dir = join(j_dir, 'debian'),
        exploded_image = j_exploded_image,
        src_dir = src_dir,
        download_url = j_url)

    # we need to add --ignore-missing-info to the dh_shlibdeps call, otherwise we see errors on ppc64le
    with open(join(j_dir, "debian", "rules"), "a") as rulesfile:
        rulesfile.write("\noverride_dh_shlibdeps:\n\tdh_shlibdeps --dpkg-shlibdeps-params=--ignore-missing-info\n")

    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=j_dir, env=env)

    deb_files = glob.glob(join(work_dir, '*.deb'))

    for deb_file in deb_files:
        copy(deb_file, cwd)
        remove(deb_file)

    return 0

if __name__ == "__main__":
    sys.exit(main())
