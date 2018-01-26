'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import zipfile
import tarfile
import urllib
import re
import datetime
import argparse
import codecs
import glob

from string import Template

from os import remove
from os import mkdir
from os import chdir
from os import listdir

from os.path import join
from os.path import realpath
from os.path import dirname
from os.path import basename
from os.path import exists
from os.path import isfile

from shutil import rmtree
from shutil import copytree
from shutil import move
from shutil import copy

import utils

def clone_sapmachine(target):
    sapmachine_repo = 'https://github.com/SAP/SapMachine.git'
    sapmachine_branch = 'sapmachine'
    utils.run_cmd(['git', 'clone', '-b', sapmachine_branch, '--depth', '1', sapmachine_repo, target])

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

def generate_configuration(templates_dir, major, target_dir, bin_dir, src_dir, download_url):
    tools = [f for f in listdir(bin_dir) if isfile(join(bin_dir, f))]
    now = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

    with open(join(templates_dir, 'control'), 'r') as control_template:
        with open(join(target_dir, 'control'), 'w+') as control_out:
            control_out.write(Template(control_template.read()).substitute(major=major))

    with open(join(templates_dir, 'install'), 'r') as install_template:
        with open(join(target_dir, 'install'), 'w+') as install_out:
            install_out.write(Template(install_template.read()).substitute(major=major))

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

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the tag to create the debian packages from', metavar='TAG', required=True)
    parser.add_argument('-d', '--templates-directory', help='specify the templates directory', metavar='DIR', required=True)
    args = parser.parse_args()

    templates_dir = realpath(args.templates_directory)
    tag = args.tag
    cwd = os.getcwd()
    work_dir = join(cwd, 'deb_work')
    version, major, build_number, sap_build_number = utils.sapmachine_tag_components(tag)
    version = version.replace('-', '.')
    jdk_name = str.format('sapmachine-{0}-jdk-{1}', major, version)
    jre_name = str.format('sapmachine-{0}-jre-{1}', major, version)

    jdk_url, jre_url = utils.fetch_tag(tag, 'linux-x64', utils.get_github_api_accesstoken())

    utils.remove_if_exists(work_dir)
    mkdir(work_dir)

    jdk_archive = join(work_dir, jdk_url.rsplit('/', 1)[-1])
    jre_archive = join(work_dir, jre_url.rsplit('/', 1)[-1])

    utils.download_artifact(jdk_url, jdk_archive)
    utils.download_artifact(jre_url, jre_archive)

    clone_sapmachine(join(work_dir, 'sapmachine_master'))
    src_dir = join(work_dir, 'sapmachine_master')

    jdk_dir = join(work_dir, jdk_name)
    jre_dir = join(work_dir, jre_name)

    mkdir(jdk_dir)
    mkdir(jre_dir)

    utils.extract_archive(jdk_archive, jdk_dir)
    utils.extract_archive(jre_archive, jre_dir)

    env = os.environ.copy()
    env['DEBFULLNAME'] = 'SapMachine'
    env['DEBEMAIL'] = 'sapmachine@sap.com'
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jdk_dir, env=env)
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jre_dir, env=env)

    generate_configuration(
        templates_dir=join(templates_dir, 'jre'),
        major=major,
        target_dir=join(jre_dir, 'debian'),
        bin_dir=join(jre_dir, 'sapmachine-jre-' + major, 'bin'),
        src_dir=src_dir,
        download_url=jre_url)

    generate_configuration(
        templates_dir=join(templates_dir, 'jdk'),
        major=major,
        target_dir=join(jdk_dir, 'debian'),
        bin_dir=join(jdk_dir, 'sapmachine-jdk-' + major, 'bin'),
        src_dir=src_dir,
        download_url=jdk_url)

    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jre_dir, env=env)
    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jdk_dir, env=env)

    deb_files = glob.glob(join(work_dir, '*.deb'))

    for deb_file in deb_files:
        copy(deb_file, cwd)
        remove(deb_file)

    rmtree(work_dir)

if __name__ == "__main__":
    sys.exit(main())