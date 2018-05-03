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
import json

from urllib2 import urlopen, Request, quote
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

def sapmachine_asset_pattern():
    return '[^-]+-([^-]+)-([^_]+)_([^_]+)_bin\.tar\.gz'

def fetch_tag(tag, platform, token=None):
    github_api = str.format('https://api.github.com/repos/SAP/SapMachine/releases/tags/{0}', quote(tag))
    jre_url = None
    jdk_url = None
    error_msg = str.format('failed to fetch assets for tag "{0}" and platform="{1}', tag, platform)

    request = Request(github_api)

    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    try:
        response = json.loads(urlopen(request).read())
        asset_pattern = re.compile(sapmachine_asset_pattern())

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

                    print(str.format('found {0} image with version={1} and platform={2}',
                        asset_image_type,
                        asset_version,
                        asset_platform))

                    if asset_image_type == 'jdk' and asset_platform == platform:
                        jdk_url = download_url
                    elif asset_image_type == 'jre' and asset_platform == platform:
                        jre_url = download_url
    except Exception:
        raise Exception(error_msg)

    if jdk_url is None or jre_url is None:
        raise Exception(error_msg)

    return jdk_url, jre_url

def sapmachine_tag_pattern():
    return '(sapmachine)-(((([0-9]+)((\.([0-9]+))*)?)\+([0-9]+))(-([0-9]+))?)(\-((\S)+))?'

def sapmachine_tag_components(tag, multiline=False):
    pattern = re.compile(sapmachine_tag_pattern())

    if multiline:
        match = re.search(pattern, tag)
    else:
        match = pattern.match(tag)

    if match is None:
        return None, None, None, None, None, None

    version = match.group(2)
    version_part = match.group(4)
    major = match.group(5)
    build_number = match.group(9)

    if len(match.groups()) >= 11:
        sap_build_number = match.group(11)
    else:
        sap_build_number = ''

    if len(match.groups()) >= 13:
        os_ext = match.group(13)
    else:
        os_ext = ''

    return version, version_part, major, build_number, sap_build_number, os_ext

def sapmachine_version_pattern():
    return '(((([0-9]+)((\.([0-9]+))*)?)(-ea)?\+([0-9]+))-sapmachine(-([0-9]+))?)'

def sapmachine_version_components(version_in, multiline=False):
    pattern = re.compile(sapmachine_version_pattern())

    if multiline:
        match = re.search(pattern, version_in)
    else:
        match = pattern.match(version_in)

    if match is None:
        return None, None, None, None, None

    version = match.group(2)
    version_part = match.group(3)
    major = match.group(4)
    build_number = match.group(9)

    if len(match.groups()) >= 11:
        sap_build_number = match.group(11)
        version += '-' + sap_build_number
    else:
        sap_build_number = ''

    return version, version_part, major, build_number, sap_build_number

def get_github_api_accesstoken():
    key = 'GITHUB_API_ACCESS_TOKEN'
    if key in os.environ:
        return os.environ[key]
    return None

def git_clone(repo, branch, target):
    git_user = os.environ['GIT_USER']
    git_password = os.environ['GIT_PASSWORD']
    remove_if_exists(target)
    run_cmd(['git', 'clone', '-b', branch, str.format('https://{0}:{1}@{2}', git_user, git_password, repo), target])

def git_commit(dir, message, to_add):
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']

    for e in to_add:
        run_cmd(['git', 'add', e], cwd=dir)

    try:
        run_cmd(['git', 'commit', '-m', message], cwd=dir, env=env)
    except Exception:
        print('git commit failed')

def git_push(dir):
    try:
        run_cmd(['git', 'fetch'], cwd=dir)
        run_cmd(['git', 'rebase'], cwd=dir)
        run_cmd(['git', 'push'], cwd=dir)
    except Exception:
        print('git push failed')
