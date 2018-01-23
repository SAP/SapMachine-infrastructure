'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import zipfile
import tarfile
import gzip
import re

from os import remove
from os.path import join
from os.path import exists
from shutil import rmtree
from shutil import move

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

def download_artifact(url, target):
    import urllib

    if exists(target):
        remove(target)

    with open(target,'wb') as file:
        print(str.format('Downloading {0} ...', url))
        file.write(urllib.urlopen(url, proxies={}).read())

def make_tgz_archive(src, dest, arcname=None):
    if exists(dest):
        remove(dest)

    archive = tarfile.open(dest, "w:gz", compresslevel=9)
    archive.add(src, arcname=arcname)
    archive.close()

def make_gz_archive(src, dest):
    if exists(dest):
        remove(dest)

    archive = gzip.open(dest, "w", compresslevel=9)

    with open(src, 'r') as src_file:
        archive.write(src_file.read())

    archive.close()

def make_zip_archive(src, dest, top_dir):
    if exists(dest):
        rmtree(top_dir)

    zip = zipfile.ZipFile(dest, 'w')

    for root, dirs, files in os.walk(src):
        for file in files:
            zip.write(join(root, file),
                      join(top_dir, os.path.relpath(join(root, file), src)),
                      zipfile.ZIP_DEFLATED)
    zip.close()

def which(file):
    for path in os.environ['PATH'].split(os.pathsep):
        if exists(join(path, file)):
                return join(path, file)

    return None

def remove_if_exists(path):
    if exists(path):
        if os.path.isdir(path):
            rmtree(path)
        else:
            remove(path)

def copytree(source, dest):
    for root, dirs, files in os.walk(source, topdown=False):
        for file in files:
            full_path = join(root, file)
            rel_path = os.path.relpath(root, start=source)
            dest_path = os.path.join(dest, rel_path, file)
            dest_dir = os.path.dirname(dest_path)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            shutil.copyfile(full_path, dest_path)

def fetch_tag(tag, platform, token=None):
    import json
    from urllib2 import urlopen, Request, quote

    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases/tags/{2}', org, repository, quote(tag))
    jre_url = None
    jdk_url = None

    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    response = json.loads(urlopen(request).read())
    asset_pattern = re.compile('[^-]+-([^-]+)-([^_]+)_([^_]+)_bin\.tar\.gz')

    if 'assets' in response:
        assets = response['assets']
        for asset in assets:
            name = asset['name']
            download_url = asset['browser_download_url']
            match = asset_pattern.match(name)

            if match is not None:
                asset_image_type = match.group(1)
                asset_version = match.group(2)
                asset_platform = match.group(3)

                if asset_image_type == 'jdk' and asset_platform == platform:
                    jdk_url = download_url
                else:
                    jre_url = download_url

    return jdk_url, jre_url

def sapmachine_tag_pattern():
    return '([^-]+)-(((([0-9]+)((\.([0-9]+))*)?)\+([0-9]+))(-([0-9]+))?)'

def sapmachine_tag_components(tag):
    pattern = re.compile(sapmachine_tag_pattern())
    match = pattern.match(tag)

    version = match.group(2)
    major = match.group(5)
    build_number = match.group(9)

    if len(match.groups()) == 11:
        sap_build_number = match.group(11)
    else:
        sap_build_number = ''

    return version, major, build_number, sap_build_number

def get_github_api_accesstoken():
    key = 'GITHUB_API_ACCESS_TOKEN'
    if key in os.environ:
        return os.environ[key]
    return None