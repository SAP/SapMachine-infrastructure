'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import json
import os
import re
import sys
import utils

from os.path import join
from string import Template
from versions import Tag

sapMachinePushURL= str.format('https://github.com/SAP/SapMachine.git',
    os.environ['GIT_USER'], os.environ['GIT_PASSWORD'])

os_description = {
    'linux.gtk.x86_64.':       { 'ordinal': 2, 'name': 'Linux x64 GTK' },
    'macosx.cocoa.aarch64':    { 'ordinal': 6, 'name': 'MacOS aarch64 Cocoa'},
    'macosx.cocoa.x86_64':     { 'ordinal': 6, 'name': 'MacOS x64 Cocoa'},
    'win32.win32.x86_64':      { 'ordinal': 8, 'name': 'Windows x64'},
}



latest_template = '''---
layout: default
title: Latest JMC ${major} Release
redirect_to:
  - ${url}
---
'''

class JmcTag(Tag):
    tag_pattern = re.compile('((\d+\.((\d+)*\.(\d+)*))-(\S+))-sap$')

    @staticmethod
    def from_string(string):
        match = JmcTag.tag_pattern.match(string)
        if match is not None:
            if match.group(6) != "SNAPSHOT":
                return JmcTag(match)
        return None

    def __init__(self, match):
        #for i in range(0, (len(match.groups()) + 1)):
        #    print(str.format("{0}. group: {1}", i, match.group(i)))
        
        self.tag = match.group(1)
        self.version_string = match.group(1)
        self.version_string_without_build = match.group(2)
        self.version = Tag.calc_version(self.version_string_without_build)
        self.build_number = 0

        if 'ga' == match.group(6):
            self.ga = True
        else:
            self.ga = False
            
    def as_string(self):
        return str.format('jmc-{0}', self.tag)            

                    
class JmcMajorVersion:
    def __init__(self, major):
        self.major = major
        self.lts = False
        self.release = None
        self.prerelease = None

    def is_released(self):
        return self.release is not None

    def is_lts(self):
        return self.lts

    def get_release_object_to_update_if_tag_is_newer(self, tag, prerelease, url):
        
        if (prerelease):
            if self.prerelease is None or tag.is_greater_than(self.prerelease.tag):
                self.prerelease = Release(tag, url)
                return self.prerelease
        else:
            if self.release is None or tag.is_greater_than(self.release.tag):
                self.release = Release(tag, url)
                return self.release

        return None

    def add_to_release_json(self, json_root):
        if self.release is not None:
            json_root['majors'].append({'id': 'jmc_' + str(self.major), 'label': str.format('JMC {0}', self.major), 'lts': self.lts, 'ea': False})
            json_root['assets']['jmc_' + str(self.major)] = self.release.to_release_json()

        if self.prerelease is not None:
            id = str(self.major) + "-ea"
            json_root['majors'].append({'id': 'jmc_' + id, 'label': str.format('JMC {0}', self.major), 'lts': self.lts, 'ea': True})
            json_root['assets']['jmc_' + id] = self.prerelease.to_release_json()


class Release:
    def __init__(self, tag, url):
        self.tag = tag
        self.url = url
        self.assets = {}
        self.assets['urls'] = {}
        
    def add_asset(self, os, asset_url):
        
        self.assets['urls'][os] = asset_url

    def to_release_json(self):
        json_root = {
            'releases': []
        }
        release_json = {
            'tag': self.tag.as_string()
        }
        release_json['urls'] = {}
        for os in self.assets['urls']:
            release_json['urls'][os] = self.assets['urls'][os]
        json_root['releases'].append(release_json)
        return json_root

def push_to_git(files):
    local_repo = join(os.getcwd(), 'gh-pages')
    if not os.path.exists(local_repo):
        utils.run_cmd("git clone --branch gh-pages --single-branch https://github.com/SAP/SapMachine.git gh-pages".split(' '))
    else:
        utils.run_cmd("git pull origin gh-pages".split(' '), cwd=local_repo)

    commits = False
    for _file in files:
        location = join(local_repo, _file['location'])
        if not os.path.exists(os.path.dirname(location)):
            os.makedirs(os.path.dirname(location))
        with open(location, 'w+') as out:
            out.write(_file['data'])
        _, diff, _  = utils.run_cmd("git diff".split(' '), cwd=local_repo, std=True)
        if diff.strip():
            utils.git_commit(local_repo, _file['commit_message'], [location])
            commits = True
    if commits:
        utils.run_cmd(str.format('git push {0}', sapMachinePushURL).split(' '), cwd=local_repo)

def main(argv=None):
    print("Querying GitHub for JMC releases...")
    sys.stdout.flush()
    releases = utils.github_api_request('releases', repository='JMC', per_page=100)
    print("Done.")

    asset_pattern = re.compile('sap\.jmc-((\d+\.(\d+)*\.(\d+)*))([-SNAPSHOT]*)-([^-]+)(\.tar\.gz|\.zip|\.msi|\.dmg)$')
    release_dict = {}
    for release in releases:
        jmcTag = JmcTag.from_string(release['name'])
        
        if jmcTag is None:
            print(str.format("{0} is no JMC release, dropping", release['name']))
            continue

        major = jmcTag.get_major()
        if not major in release_dict:
            jmcVersion = JmcMajorVersion(major)
            release_dict[major] = jmcVersion
        else:
            jmcVersion = release_dict[major]

        jmcRelease = jmcVersion.get_release_object_to_update_if_tag_is_newer(jmcTag, release['prerelease'], release['html_url'])

        if jmcRelease is None:
            print(str.format("{0} skipped because newer version available", release['name']))
            continue

        print("found JMC release: {0}", release['name'])
        for asset in release['assets']:
            match = asset_pattern.match(asset['name'])
            if match is None:
                continue

            os = match.group(6)
            file_type = match.group(7)

            targetOs = os
            if os == 'linux.gtk.x86_64':
                targetOs = 'linux-x64'
            elif os == 'macosx.cocoa.aarch64':
                targetOs = 'macos-aarch64'
            elif os == 'macosx.cocoa.x86_64':
                targetOs = 'macos-x64'
            elif os == 'win32.win32.x86_64':
                targetOs = 'windows-x64'

            jmcRelease.add_asset(targetOs, asset['browser_download_url'])

    # reduce releases dictionary by removing obsolete versions
    # Keep LTS versions, latest release and the release that is currently in development
    latest_released_version = 0
    for major in list(release_dict.keys()):
        if not release_dict[major].is_released():
            continue
        if major > latest_released_version:
            if latest_released_version > 0 and not release_dict[latest_released_version].is_lts():
                del release_dict[latest_released_version]
            latest_released_version = major
        elif not release_dict[major].is_lts():
            del release_dict[major]

    json_root = {
        'majors':[],
        'assets':{}
    }

    release_dict = dict(sorted(release_dict.items(), key = lambda x:x[0], reverse = True))

    for major in release_dict:
        release_dict[major].add_to_release_json(json_root)

    files = [{
        'location': join('assets', 'data', 'jmc_releases.json'),
        'data': json.dumps(json_root, indent=4) + '\n',
        'commit_message': 'Updated release data.'
    }]

    for major in release_dict:
        if not release_dict[major].is_released():
            continue

        files.append({
            'location': join('latest', 'jmc' + str(major), 'index.md'),
            'data': Template(latest_template).substitute(
                major = major,
                url = release_dict[major].release.url
            ),
            'commit_message': str.format('Updated latest link for JMC {0}', major)
        })

    push_to_git(files)

    return 0

if __name__ == "__main__":
    sys.exit(main())


