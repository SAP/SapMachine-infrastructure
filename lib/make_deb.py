'''
Copyright (c) 2017-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import codecs
import datetime
import glob
import os
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
    parser.add_argument('-t', '--tag', help='SapMachine version tag to create the debian packages for', metavar='TAG', required=True)
    parser.add_argument('-d', '--download', help='Does artifact and git repo need to be downloaded', action='store_true')
    parser.add_argument('-a', '--architecture', help='specifies the architecture (linux-aarch64, linux-ppc64le, linux-x64)', metavar='ARCH', default='linux-x64')
    args = parser.parse_args()

    cwd = os.getcwd()
    work_dir = join(cwd, 'deb_work')
    tag = SapMachineTag.from_string(args.tag)
    version = tag.get_version_string().replace('-', '.')
    jdk_name = str.format('sapmachine-{0}-jdk-{1}', tag.get_major(), version)
    jdk_url = utils.get_asset_urls(tag, args.architecture, ["jdk"])['jdk']

    utils.remove_if_exists(work_dir)
    mkdir(work_dir)

    if args.download:
        jdk_archive = join(work_dir, jdk_url.rsplit('/', 1)[-1])
        utils.download_artifact(jdk_url, jdk_archive)
    else:
        jdk_archive = join(cwd, jdk_url.rsplit('/', 1)[-1])

    jdk_dir = join(work_dir, jdk_name)
    mkdir(jdk_dir)
    utils.extract_archive(jdk_archive, jdk_dir)

    if args.download:
        src_dir = join(work_dir, 'sapmachine_master')
        utils.git_clone('github.com/SAP/SapMachine', args.tag, src_dir)
    else:
        src_dir = join(cwd, 'SapMachine')

    env = os.environ.copy()
    env['DEBFULLNAME'] = 'SapMachine'
    env['DEBEMAIL'] = 'sapmachine@sap.com'
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jdk_dir, env=env)

    jdk_exploded_image = glob.glob(join(jdk_dir, 'sapmachine-*'))[0]

    generate_configuration(
        templates_dir=join(realpath("SapMachine-Infrastructure/debian-templates"), 'jdk'),
        major=str(tag.get_major()),
        arch = "arm64" if args.architecture == "linux-aarch64" else ("ppc64el" if args.architecture == "linux-ppc64le" else "amd64"),
        target_dir=join(jdk_dir, 'debian'),
        exploded_image=jdk_exploded_image,
        src_dir=src_dir,
        download_url=jdk_url)

    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jdk_dir, env=env)

    deb_files = glob.glob(join(work_dir, '*.deb'))

    for deb_file in deb_files:
        copy(deb_file, cwd)
        remove(deb_file)

    return 0

if __name__ == "__main__":
    sys.exit(main())
