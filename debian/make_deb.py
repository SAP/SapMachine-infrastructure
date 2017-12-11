import os
import sys
import shutil
import zipfile
import tarfile
import urllib
import glob
import re
import datetime

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

def run_cmd(cmdline, throw=True, cwd=None, env=None, std=False, shell=False):
    import subprocess

    print str.format('calling {0}', cmdline)
    if std:
        subproc = subprocess.Popen(cmdline, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        out, err = subproc.communicate()
    else:
        subproc = subprocess.Popen(cmdline, cwd=cwd, env=env, shell=shell)
    retcode = subproc.wait()
    if throw and retcode != 0:
        raise Exception(str.format('command failed with exit code {0}: {1}', retcode, cmdline))
    if std:
        return (retcode, out, err)
    return retcode

def extract_archive(archive, target):
    if archive.endswith('.zip'):
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            print(str.format('Extracting zip archive {0} ...', archive))
            zip_ref.extractall(target)

        remove(archive)
    elif archive.endswith('tar.gz'):
        print(str.format('Extracting tar.gz archive {0} ...', archive))
        with tarfile.open(archive, 'r') as tar_ref:
            tar_ref.extractall(target)

        remove(archive)
    else:
        move(archive, target)

def clone_sapmachine(target):
    sapmachine_repo = 'https://github.com/SAP/SapMachine.git'
    run_cmd(['git', 'clone', '-b', 'master', sapmachine_repo, target])

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

def download(url, target):
    if exists(target):
        remove(target)

    print(str.format('Downloading {0} ...', url))

    with open(target, 'w+') as f:
        f.write(urllib.urlopen(url, proxies={}).read())

def generate_configuration(templates_dir, tag, target_dir, bin_dir, license_file, download_url):
    pattern = re.compile('jdk-([0-9]+)\+[0-9]+')
    major = pattern.match(tag).group(1)
    tools = [f for f in listdir(bin_dir) if isfile(join(bin_dir, f))]

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

    copy(join(templates_dir, 'control'), join(target_dir, 'control'))


def main(argv=None):
    cwd = os.getcwd()

    work_dir = join(cwd, 'deb_work')
    tag = 'jdk-10+34'
    version = tag.rsplit('-', 1)[-1]
    templates_dir = join(cwd, 'templates')
    jdk_name = str.format('sapmachine-jdk-{0}', version)
    jre_name = str.format('sapmachine-jre-{0}', version)

    jdk_url, jre_url = fetch_tag(tag)

    if exists(work_dir):
        rmtree(work_dir)

    mkdir(work_dir)

    jdk_archive = join(work_dir, jdk_url.rsplit('/', 1)[-1])
    jre_archive = join(work_dir, jre_url.rsplit('/', 1)[-1])

    download(jdk_url, jdk_archive)
    download(jre_url, jre_archive)

    clone_sapmachine(join(work_dir, 'sapmachine_master'))
    license_file = join(work_dir, 'sapmachine_master', 'LICENSE')

    jdk_dir = join(work_dir, jdk_name)
    jre_dir = join(work_dir, jre_name)

    mkdir(jdk_dir)
    mkdir(jre_dir)

    extract_archive(jdk_archive, jdk_dir)
    extract_archive(jre_archive, jre_dir)

    run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jdk_dir)
    run_cmd(['dh_make', '-n', '-s', '-y'], cwd=jre_dir)

    generate_configuration(join(templates_dir, 'jre'), tag, join(jre_dir, 'debian'), join(jre_dir, 'jre', 'bin'), license_file, jdk_url)
    generate_configuration(join(templates_dir, 'jdk'), tag, join(jdk_dir, 'debian'), join(jdk_dir, 'jdk', 'bin'), license_file, jre_url)

    run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jre_dir)
    run_cmd(['debuild', '-b', '-uc', '-us'], cwd=jdk_dir)

    deb_files = glob.glob(join(work_dir, '*.deb'))

    for deb_file in deb_files:
        copy(deb_file, cwd)
        remove(deb_file)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))