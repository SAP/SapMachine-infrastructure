import os
import sys
import shutil
import zipfile
import tarfile
import urllib
import glob
import re
import datetime
import argparse

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

def fetch_tag(tag):
    import json

    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases/tags/{2}', org, repository, urllib.quote(tag))
    jre_url = None
    jdk_url = None

    response = json.loads(urllib.urlopen(github_api, proxies={}).read())

    if 'assets' in response:
        assets = response['assets']
        for asset in assets:
            name = asset['name']
            download_url = asset['browser_download_url']
            if name.endswith('tar.gz'):
                if 'jre' in name:
                    # JRE
                    jre_url = download_url
                else:
                    # JDK
                    jdk_url = download_url

    return jdk_url, jre_url

def generate_configuration(templates_dir, major, target_dir, bin_dir, license_file, download_url):
    tools = [f for f in listdir(bin_dir) if isfile(join(bin_dir, f))]

    with open(join(templates_dir, 'control'), 'r') as control_template:
        with open(join(target_dir, 'control'), 'w+') as control_out:
            control_out.write(Template(control_template.read()).substitute(major=major))

    with open(join(templates_dir, 'install'), 'r') as install_template:
        with open(join(target_dir, 'install'), 'w+') as install_out:
            install_out.write(Template(install_template.read()).substitute(major=major))

    with open(join(templates_dir, 'postinst'), 'r') as postinst_template:
        with open(join(target_dir, 'postinst'), 'w+') as postinst_out:
            postinst_out.write(Template(postinst_template.read()).substitute(tools=' '.join([tool for tool in tools])))

    with open(join(templates_dir, '..', 'copyright'), 'r') as copyright_template:
        with open(license_file, 'r') as license_in:
            with open(join(target_dir, 'copyright'), 'w+') as copyright_out:
                now = datetime.datetime.utcnow().isoformat()
                template = Template(copyright_template.read())
                copyright_out.write(template.substitute(
                    date_and_time=now,
                    download_url=download_url,
                    license=license_in.read()
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
    pattern = re.compile('(jdk|sapmachine)-(([0-9]+)\+[0-9])+')
    match = pattern.match(tag)
    version = match.group(2)
    major = match.group(3)
    jdk_name = str.format('sapmachine-{0}-jdk-{1}', major, version)
    jre_name = str.format('sapmachine-{0}-jre-{1}', major, version)

    jdk_url, jre_url = fetch_tag(tag)

    if exists(work_dir):
        rmtree(work_dir)

    mkdir(work_dir)

    jdk_archive = join(work_dir, jdk_url.rsplit('/', 1)[-1])
    jre_archive = join(work_dir, jre_url.rsplit('/', 1)[-1])

    utils.download_artifact(jdk_url, jdk_archive)
    utils.download_artifact(jre_url, jre_archive)

    clone_sapmachine(join(work_dir, 'sapmachine_master'))
    license_file = join(work_dir, 'sapmachine_master', 'LICENSE')

    jdk_dir = join(work_dir, jdk_name)
    jre_dir = join(work_dir, jre_name)

    mkdir(jdk_dir)
    mkdir(jre_dir)

    utils.extract_archive(jdk_archive, jdk_dir)
    utils.extract_archive(jre_archive, jre_dir)

    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jdk_dir)
    utils.run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jre_dir)

    generate_configuration(
        templates_dir=join(templates_dir, 'jre'),
        major=major,
        target_dir=join(jre_dir, 'debian'),
        bin_dir=join(jre_dir, 'jre', 'bin'),
        license_file=license_file,
        download_url=jdk_url)

    generate_configuration(
        templates_dir=join(templates_dir, 'jdk'),
        major=major,
        target_dir=join(jdk_dir, 'debian'),
        bin_dir=join(jdk_dir, 'jdk', 'bin'),
        license_file=license_file,
        download_url=jre_url)

    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jre_dir)
    utils.run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jdk_dir)

    deb_files = glob.glob(join(work_dir, '*.deb'))

    for deb_file in deb_files:
        copy(deb_file, cwd)
        remove(deb_file)

    rmtree(work_dir)

if __name__ == "__main__":
    sys.exit(main())