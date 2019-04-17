'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import tarfile
import gzip
import re
import json
import platform
from zipfile import ZipFile, ZipInfo

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

'''
    Preserves the executable bits
'''
class SafeZipFile(ZipFile):
    def extract(self, member, path=None, pwd=None):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        ret_val = self._extract_member(member, path, pwd)
        attr = member.external_attr >> 16
        os.chmod(ret_val, attr)
        return ret_val

def extract_archive(archive, target, remove_archive=True):
    if archive.endswith('.zip'):
        with SafeZipFile(archive) as zip_ref:
            print(str.format('Extracting zip archive {0} ...', archive))
            zip_ref.extractall(target)

        if remove_archive:
            remove(archive)
    elif archive.endswith('tar.gz'):
        print(str.format('Extracting tar.gz archive {0} ...', archive))
        with tarfile.open(archive, 'r') as tar_ref:
            tar_ref.extractall(target)

        if remove_archive:
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

def sapmachine_is_lts(major):
    lts_releases = [
        '11',
        '18'
    ]
    return major in lts_releases

def sapmachine_tag_pattern():
    return '(sapmachine)-((((\d+)((\.(\d+))*)?)(\+(\d+))?)(-(\d+))?)(\-((\S)+))?'

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

    if len(match.groups()) >= 10:
        build_number = match.group(10)
    else:
        build_number = ''

    if len(match.groups()) >= 12:
        sap_build_number = match.group(12)
    else:
        sap_build_number = ''

    if len(match.groups()) >= 13:
        os_ext = match.group(13)
    else:
        os_ext = ''

    if not sap_build_number:
        version_parts = version_part.split('.')
        if len(version_parts) >= 5:
            sap_build_number = version_parts[4]

    return version, version_part, major, build_number, sap_build_number, os_ext

def sapmachine_version_pattern():
    return '((((\d+)((\.(\d+))*)?)(-ea)?(-snapshot)?\+(\d+))(-LTS)?-sapmachine(-(\d+))?)'

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

    if len(match.groups()) >= 12:
        sap_build_number = match.group(12)
        #version += '-' + sap_build_number
    else:
        version_parts = version_part.split('.')
        if len(version_parts) >= 5:
            sap_build_number = version_parts[4]

    return version, version_part, major, build_number, sap_build_number

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

def git_tag(dir, tag_name):
    try:
        run_cmd(['git', 'tag', tag_name], cwd=dir)
    except Exception:
        print('git tag failed')

def git_push(dir):
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']

    try:
        run_cmd(['git', 'fetch'], cwd=dir)
        run_cmd(['git', 'rebase'], cwd=dir, env=env)
        run_cmd(['git', 'push'], cwd=dir, env=env)
    except Exception:
        print('git push failed')

def git_push_tag(dir, tag_name):
    try:
        run_cmd(['git', 'push', 'origin', tag_name], cwd=dir)
    except Exception:
        print('git push tag failed')

def get_github_api_accesstoken():
    key = 'GITHUB_API_ACCESS_TOKEN'
    if key in os.environ:
        return os.environ[key]
    return None

def github_api_request(api=None, url=None, owner='SAP', repository='SapMachine', data=None, method='GET', per_page=None, content_type=None):
    load_next = True
    result = None
    token = get_github_api_accesstoken()
    link_pattern = re.compile('(<([^>]*)>; rel=\"prev\",\s*)?(<([^>]*)>; rel=\"next\",\s)?(<([^>]*)>; rel=\"last\"\s*)?')

    if api is None and url is None:
        return None

    while load_next:
        if url is None:
            url_parameter = ''
            if per_page is not None:
                url_parameter = str.format('?per_page={0}', per_page)
            url = str.format('https://api.github.com/repos/{0}/{1}/{2}{3}', owner, repository, api, url_parameter)

        request = Request(url, data=data)
        request.get_method = lambda: method

        if token is not None:
            request.add_header('Authorization', str.format('token {0}', token))

        if content_type is not None:
            request.add_header('Content-Type', content_type)

        if data is not None:
            request.add_header('Content-Length', len(data))

        try:
            response = urlopen(request)
            link = response.info().getheader('Link')

            if result is None:
                result = json.loads(response.read())
            else:
                result.extend(json.loads(response.read()))

            load_next = False

            if link is not None and method == 'GET':
                match = re.search(link_pattern, link)

                if match is not None:
                    next_url = match.group(4)
                    last_url = match.group(6)

                    if next_url != last_url:
                        url = next_url
                        load_next = True

        except Exception as e:
            print(str.format('{0}: "{1}"', url, e))
            return None

    return result

def sapmachine_asset_pattern():
    return '[^-]+-([^-]+)-([^_]+)_([^_]+)_bin(\.tar\.gz|\.zip|\.msi)'

def get_asset_url(tag, platform):
    jre_url = None
    jdk_url = None
    error_msg = str.format('failed to fetch assets for tag "{0}" and platform="{1}', tag, platform)

    try:
        asset_pattern = re.compile(sapmachine_asset_pattern())
        release = github_api_request(str.format('releases/tags/{0}', quote(tag)), per_page=100)

        if 'assets' in release:
            assets = release['assets']
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
    except Exception as e:
        print(e)
        raise Exception(error_msg)

    if jdk_url is None or jre_url is None:
        raise Exception(error_msg)

    return jdk_url, jre_url

def sapmachine_tag_is_release(tag):
    response = github_api_request('releases')

    for release in response:
        if release['tag_name'] == tag:
            return not release['prerelease']

    return False

class JDKTag:
    jdk_tag_pattern = re.compile('jdk-((\d+)(\.\d+)*)(\+\d+|-ga)$')

    def __init__(self, match):
        self.tag = match.group(0)
        self.version_string = match.group(1)
        self.version = match.group(1).split('.')
        self.build_number = match.group(4)[1:]
        self.tag_is_ga = self.build_number == 'ga'

        if self.tag_is_ga:
            self.build_number = 999999
        else:
            self.build_number = int(self.build_number)

        self.version = map(int, self.version)
        self.version.extend([0 for i in range(5 - len(self.version))])

        self.sapmachine_tag = None

    def as_string(self):
        return self.tag


    def as_sapmachine_tag(self):
        if self.sapmachine_tag == None:
            self.sapmachine_tag = str.format('sapmachine-{0}{1}',
                self.version_string,
                '' if self.tag_is_ga else '+' + str(self.build_number))
        return self.sapmachine_tag

    def get_version(self):
        return self.version

    def get_major(self):
        return self.version[0]

    def get_build_number(self):
        return self.build_number

    def is_ga(self):
        return self.tag_is_ga

    def equals(self, other):
        return self.tag == other.tag

    def is_greater_than(self, other):
        ts = tuple(self.version)
        to = tuple(other.get_version())
        ts += (self.build_number,)
        to += (other.get_build_number(),)
        return ts > to

def get_system():
    system = platform.system().lower()

    if system.startswith('msys') or system.startswith('cygwin') or system.startswith('win'):
        return 'windows'
    elif system == 'darwin':
        return 'osx'
    else:
        return system

def get_arch():
    arch = platform.machine().lower()

    if arch == 'x86_64':
        return 'x64'
    else:
        return arch