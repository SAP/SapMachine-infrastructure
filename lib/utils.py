'''
Copyright (c) 2017-2024 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import gzip
import json
import os
import pickle
import platform
import re
import requests
import shutil
import sys
import tarfile
import time
import zipfile

from os import remove
from os.path import exists
from os.path import join
from shutil import move
from shutil import rmtree
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen, Request
from versions import SapMachineTag
from zipfile import ZipFile, ZipInfo

def save_dictionary_to_file(dictionary, filename):
    with open(filename, 'wb') as file:
        pickle.dump(dictionary, file)

def load_dictionary_from_file(filename):
    with open(filename, 'rb') as file:
        dictionary = pickle.load(file)
    return dictionary

def file_exists_and_is_younger_than_an_hour(filename):
    if not exists(filename):
        return False

    one_hour = 60 * 60  # 1 hour in seconds

    # Get the current time
    current_time = time.time()

    # Get the last modified time of the file
    file_modified_time = os.path.getmtime(filename)

    # Calculate the time difference
    time_difference = current_time - file_modified_time

    # Compare the time difference with one hour
    return time_difference < one_hour

def run_cmd(cmdline, throw=True, cwd=None, env=None, std=False, shell=False, quiet=False):
    import subprocess

    if not quiet:
        print(str.format('Calling {0}', cmdline))
    if std:
        subproc = subprocess.Popen(cmdline, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        out, err = subproc.communicate()
    else:
        sys.stdout.flush()
        subproc = subprocess.Popen(cmdline, cwd=cwd, env=env, shell=shell)
    retcode = subproc.wait()
    if throw and retcode != 0:
        raise Exception(str.format('Command failed with exit code {0}: {1}', retcode, cmdline))
    if std:
        try:
            out = out.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            pass
        try:
            err = err.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            pass
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

    def extractall(self, path=None, members=None, pwd=None):
        if members is None:
            members = self.namelist()

        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)

        for zipinfo in members:
            self.extract(zipinfo, path, pwd)

def extract_archive(archive, target, remove_archive=False):
    if archive.endswith('.zip'):
        with SafeZipFile(archive) as zip_ref:
            print(f"Extracting zip archive {archive}...")
            zip_ref.extractall(target)

        if remove_archive:
            remove(archive)
    elif archive.endswith('tar.gz'):
        print(f"Extracting tar.gz archive {archive}...")
        with tarfile.open(archive, 'r') as tar_ref:
            tar_ref.extractall(target)

        if remove_archive:
            remove(archive)
    else:
        move(archive, target)

def download_file(url, target, headers={}):
    print(f"Downloading {url} to {target}...")

    if exists(target):
        remove(target)

    if 'GIT_PASSWORD' in os.environ and 'Authorization' not in headers:
        headers['Authorization'] = f"token {os.environ['GIT_PASSWORD']}"

    response = requests.get(url, headers=headers, stream=True)

    if response.status_code == 200:
        with open(target, 'wb') as file:
            # Iterate over the content in chunks to avoid loading the entire file into memory
            for chunk in response.iter_content(chunk_size=512):
                file.write(chunk)
    else:
        raise Exception(f"Download failed: {response.status_code}")

def download_github_release_assets(release_name, api='https://api.github.com', org='SAP', repo='SapMachine', destination='tmp'):
    if not os.path.exists(destination):
        os.makedirs(destination)

    assets = github_api_request(api=f"releases/tags/{release_name}", github_api_url=api, github_org=org, repository=repo)
    for asset in assets["assets"]:
        download_file(asset["url"], os.path.join(destination, asset["name"]), {'Accept': 'application/octet-stream'})

def download_text(url):
    headers = {'Authorization': f"token {os.environ['GIT_PASSWORD']}" } if 'GIT_PASSWORD' in os.environ else None
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Downloading {url} failed: {response.status_code}")

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
        data = src_file.read()
        if type(data) == str:
            data = data.encode('utf-8')
        archive.write(data)

    archive.close()

def make_zip_archive(src, dest, top_dir):
    if exists(dest):
        rmtree(top_dir)

    zip = ZipFile(dest, 'w')

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
            dest_path = join(dest, rel_path, file)
            dest_dir = os.path.dirname(dest_path)

            if not exists(dest_dir):
                os.makedirs(dest_dir)

            shutil.copyfile(full_path, dest_path)

release_info = None
def read_release_info():
    global release_info
    if release_info == None:
        releases_file = os.path.abspath(join(os.path.dirname(__file__), '..', 'releases.json'))
        with open(releases_file, 'r') as file:
            release_info = json.loads(file.read())

def sapmachine_default_major():
    read_release_info()
    return release_info['head_release']

def sapmachine_dev_releases():
    read_release_info()
    return release_info['dev_releases']

def sapmachine_active_releases():
    read_release_info()
    return release_info['active_releases']

def sapmachine_is_lts(major):
    read_release_info()
    return (major if isinstance(major, int) else int(major)) in release_info['lts_releases']

def sapmachine_version_pattern():
    return r'build ((\d+)((\.(\d+))*)?)'

def sapmachine_version_components(version_in):
    pattern = re.compile(sapmachine_version_pattern())

    match = re.search(pattern, version_in)

    if match is None:
        return None, None

    version = match.group(1)
    major = match.group(2)

    return version, major

def sapmachine_branch_pattern():
    return r'sapmachine([\d]+)?(-sec)?$'

def get_active_sapmachine_branches():
    sapmachine_latest = 0
    sapmachine_branches = []

    # fetch all branches
    branches = github_api_request('branches', per_page=100)

    # iterate all branches of the SapMachine repository and filter for sapmachine<nn>
    branch_pattern = re.compile(sapmachine_branch_pattern())
    for branch in branches:
        match = branch_pattern.match(branch['name'])
        if match is not None and match.group(1) is not None:
            # found sapmachine branch
            major = int(match.group(1))
            # ignore inactive ones
            if major < 22 and major != 11 and major != 17 and major != 21:
                continue
            sapmachine_branches.append([branch['name'], major])
            sapmachine_latest = max(sapmachine_latest, major)

    # sort in descending order, this helps performance in some places
    sapmachine_branches.sort(reverse=True)

    # also add "sapmachine" branch with latest major version
    sapmachine_branches.insert(0, ["sapmachine", sapmachine_latest + 1])

    print('Active SapMachine branches: %s' % ', '.join(map(str, sapmachine_branches)))

    return sapmachine_branches

def jmc_branch_pattern():
    return r'sap([\d]+)?$'

def get_active_jmc_branches():
    jmc_latest = 0
    jmc_branches = []

    # fetch all branches
    branches = github_api_request('branches', repository='JMC', per_page=100)

    # iterate all branches of the JMC repository and filter for sap<nn>
    branch_pattern = re.compile(jmc_branch_pattern())
    for branch in branches:
        match = branch_pattern.match(branch['name'])
        if match is not None and match.group(1) is not None:
            # found JMC branch
            major = int(match.group(1))
            jmc_branches.append([branch['name'], major])
            jmc_latest = max(jmc_latest, major)

    # sort in descending order, this helps performance in some places
    jmc_branches.sort(reverse=True)

    # also add "jmc" branch with latest major version
    jmc_branches.insert(0, ["sap", jmc_latest + 1])

    print('Active JMC branches: %s' % ', '.join(map(str, jmc_branches)))

    return jmc_branches

def git_get(repo, ref, target):
    if platform.system().lower().startswith('cygwin'):
        git_tool = "/cygdrive/c/Program Files/Git/cmd/git.exe"
        _, target_mixed, _ = run_cmd(['cygpath', '-m', target], std=True)
        target_mixed = target_mixed.rstrip()
    else :
        git_tool = "git"
        target_mixed = target

    git_command = [git_tool, '--version']
    run_cmd(git_command)
    git_command = [git_tool, 'init', target]
    run_cmd(git_command)
    git_command = [git_tool, 'config', 'advice.detachedHead', 'false']
    run_cmd(git_command, cwd = target)
    git_command = [git_tool, 'fetch']
    if 'GIT_USER' in os.environ and 'GIT_PASSWORD' in os.environ:
        git_command.append(f"https://{os.environ['GIT_USER']}:{os.environ['GIT_PASSWORD']}@{repo}")
    else:
        git_command.append(f"https://{repo}")
    git_command.append(ref)
    run_cmd(git_command, cwd = target)
    git_command = [git_tool, 'checkout', 'FETCH_HEAD']
    run_cmd(git_command, cwd = target)

def git_clone(repo, branch, target):
    if platform.system().lower().startswith('cygwin'):
        git_tool = "/cygdrive/c/Program Files/Git/cmd/git.exe"
        _, target_mixed, _ = run_cmd(['cygpath', '-m', target], std=True)
        target_mixed = target_mixed.rstrip()
    else :
        git_tool = "git"
        target_mixed = target

    git_command = [git_tool, '--version']
    run_cmd(git_command)
    git_command = [git_tool, 'clone', '--single-branch', '-b', branch]
    if 'GIT_USER' in os.environ and 'GIT_PASSWORD' in os.environ:
        git_command.append(f"https://{os.environ['GIT_USER']}:{os.environ['GIT_PASSWORD']}@{repo}")
        git_fix_remote_command = [git_tool, 'remote', 'set-url', 'origin', f"https://{repo}"]
    else:
        git_command.append(f"https://{repo}")
        git_fix_remote_command = None
    git_command.append(target_mixed)

    remove_if_exists(target)
    run_cmd(git_command)
    if git_fix_remote_command is not None:
        run_cmd(git_fix_remote_command, cwd=target)

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

def git_checkout(dir, branch):
    try:
        run_cmd(['git', 'checkout', branch], cwd=dir)
    except Exception:
        print('git checkout failed')

def git_tag(dir, tag_name, tag_desc=None, force=False):
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']

    if tag_desc is None:
        tag_desc = tag_name

    if force is False:
        run_cmd(['git', 'tag', '-a', '-m', tag_desc, tag_name], cwd=dir, env=env)
    else:
        run_cmd(['git', 'tag', '-a', '-f', '-m', tag_desc, tag_name], cwd=dir, env=env)

def git_push(dir):
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']

    try:
        run_cmd(['git', 'fetch'], cwd=dir)
        run_cmd(['git', 'rebase'], cwd=dir, env=env)

        if 'GIT_USER' in os.environ and 'GIT_PASSWORD' in os.environ:
            _, giturl, _ = run_cmd(['git', 'config', '--get', 'remote.origin.url'], cwd=dir, std=True)
            pushurl = f"https://{os.environ['GIT_USER']}:{os.environ['GIT_PASSWORD']}@{giturl.rstrip().split('//')[1]}"
            run_cmd(['git', 'push', pushurl], cwd=dir, env=env)
        else:
            run_cmd(['git', 'push'], cwd=dir, env=env)
    except Exception:
        print('git push failed')

def git_push_tag(dir, tag_name, force=False):
    if 'GIT_USER' in os.environ and 'GIT_PASSWORD' in os.environ:
        _, giturl, _ = run_cmd(['git', 'config', '--get', 'remote.origin.url'], cwd=dir, std=True)
        pushurl = f"https://{os.environ['GIT_USER']}:{os.environ['GIT_PASSWORD']}@{giturl.rstrip().split('//')[1]}"
        if force is True:
            run_cmd(['git', 'push', '-f', pushurl, tag_name], cwd=dir)
        else:
            run_cmd(['git', 'push', pushurl, tag_name], cwd=dir)
    else:
        run_cmd(['git', 'push', 'origin', tag_name], cwd=dir)

def github_api_request(api=None, url=None, github_api_url='https://api.github.com', github_org='SAP', repository='SapMachine', data=None, method='GET', per_page=None, content_type=None, url_parameter=[]):
    if api is None and url is None:
        return None

    if url is None:
        if per_page is not None:
            url_parameter.append(str.format('per_page={0}', per_page))
        url_parameter_string = '?' + '&'.join(url_parameter) if len(url_parameter) > 0 else ''
        url = f'{github_api_url}/repos/{github_org}/{repository}/{api}{url_parameter_string}'
    load_next = True
    result = None
    link_pattern = None

    while load_next:
        if type(data) == str:
            data = data.encode('utf-8')

        request = Request(url, data=data)
        request.get_method = lambda: method

        if 'GIT_PASSWORD' in os.environ:
            request.add_header('Authorization', f"token {os.environ['GIT_PASSWORD']}")
        else:
            print("Warning: No GitHub credentials provided. This could quickly lead to exceeding the GitHub API rate limit.", file=sys.stderr)

        if content_type is not None:
            request.add_header('Content-Type', content_type)

        if data is not None:
            request.add_header('Content-Length', len(data))

        response = urlopen(request)
        link = response.info().get('Link')

        try:
            response = response.read().decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            response = response.read()

        if result is None:
            result = json.loads(response)
        else:
            result.extend(json.loads(response))

        if link is not None and method == 'GET':
            if link_pattern is None:
                link_pattern = re.compile(r'(<([^>]*)>; rel=\"prev\",\s*)?(<([^>]*)>; rel=\"next\",\s)?')
            match = re.search(link_pattern, link)

            if match is not None:
                next_url = match.group(4)

                if next_url is not None:
                    url = next_url
                    continue

        load_next = False

    return result

github_tags = {}
def get_github_tags(repository='SapMachine'):
    global github_tags
    if repository not in github_tags.keys() or github_tags[repository] is None:
        github_tags[repository] = github_api_request('tags', repository=repository, per_page=300)
    return github_tags[repository]

def get_sapmachine_releases(major = None):
    rel_url = f"https://sap.github.io/SapMachine/assets/data/sapmachine-releases-{'all' if major is None else str(major)}.json"
    return json.loads(download_text(rel_url)) if major is None else {str(major): json.loads(download_text(rel_url))}

def sapmachine_asset_base_pattern():
    return '[^-]+-([^-]+)-([^_]+)_([^_]+)_bin'

def sapmachine_asset_pattern():
    return sapmachine_asset_base_pattern() + r'(\.tar\.gz|\.zip|\.msi|\.dmg)$'

def sapmachine_checksum_pattern():
    return sapmachine_asset_base_pattern() + r'((|\.msi\.|\.dmg\.|\.)(sha256\.txt)|(\.sha256\.dmg\.txt))$'

def get_asset_urls(tag, platform, asset_types=["jdk", "jre"], pattern=None):
    asset_urls = {}
    try:
        release = github_api_request(f'releases/tags/{quote(tag.as_string())}', per_page=100)

        if 'assets' in release:
            asset_pattern = re.compile(sapmachine_asset_base_pattern() + pattern if pattern else sapmachine_asset_pattern())

            assets = release['assets']
            for asset in assets:
                name = asset['name']
                match = asset_pattern.match(name)

                if match is not None:
                    asset_type = match.group(1)
                    asset_version = match.group(2)
                    asset_platform = match.group(3)

                    print((str.format('Found {0} image with version={1} and platform={2}', asset_type, asset_version, asset_platform)))
                    if (asset_platform == platform and asset_type in asset_types):
                        asset_urls[asset_type] = asset['browser_download_url']

    except Exception as e:
        print(e)
        raise Exception(str.format('Failed to fetch assets for tag "{0}" and platform="{1}"', tag.as_string(), platform))

    return asset_urls

def sapmachine_tag_is_release(tag):
    try:
        release = github_api_request(f'releases/tags/{tag}')
    except HTTPError as httpError:
        return False

    if release['tag_name'] == tag:
        return not release['prerelease']

    return False

def get_system():
    system = platform.system().lower()

    if system.startswith('msys') or system.startswith('cygwin') or system.startswith('win'):
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    else:
        return system

def get_arch():
    if get_system() == "aix":
        return "ppc64"
    arch = platform.machine().lower()

    if arch == 'x86_64' or arch == 'amd64':
        return 'x64'
    elif arch == 'arm64':
        return 'aarch64'
    else:
        return arch

# Tries to calculate a value for major release from a set of strings that could be a digit, a SapMachine release tag or a sapmachine branch
# If it can't be figured out from the inputs, the result is None
def calc_major(values):
    branch_pattern = re.compile(r'sapmachine(\d+)?(-sec)?$')
    version_pattern = re.compile(r'(\d+)(\.\d+)*')
    for val in values:
        print("calc_major: checking " + val, file=sys.stderr)
        if val is None:
            continue

        if val.isdigit():
            return int(val)

        tag = SapMachineTag.from_string(val)
        if not tag is None:
            return tag.get_major()

        match = version_pattern.match(val)
        if match is not None:
            print("calc_major: Matched the version pattern " + match.group(), file=sys.stderr)
            return int(match.group(1))

        match = branch_pattern.match(val)
        if match is not None and match.group(1) is not None and match.group(1).isdigit():
            return int(match.group(1))

        if val == "sapmachine":
            return sapmachine_default_major()

    return None
