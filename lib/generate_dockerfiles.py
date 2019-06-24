'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils
import argparse

from os.path import join
from string import Template
from utils import github_api_request

dockerfile_template = '''
FROM ubuntu:18.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates gnupg2 \
    && rm -rf /var/lib/apt/lists/*

RUN export GNUPGHOME="$(mktemp -d)" \
    && wget -q -O - http://dist.sapmachine.io/debian/sapmachine.old.key | gpg --batch --import \
    && gpg --batch --export --armor 'DA4C 00C1 BDB1 3763 8608 4E20 C7EB 4578 740A EEA2' > /etc/apt/trusted.gpg.d/sapmachine.old.gpg.asc \
    && wget -q -O - http://dist.sapmachine.io/debian/sapmachine.key | gpg --batch --import \
    && gpg --batch --export --armor 'CACB 9FE0 9150 307D 1D22 D829 6275 4C3B 3ABC FE23' > /etc/apt/trusted.gpg.d/sapmachine.gpg.asc \
    && gpgconf --kill all && rm -rf "$$GNUPGHOME" \
    && echo "deb http://dist.sapmachine.io/debian/amd64/ ./" > /etc/apt/sources.list.d/sapmachine.list \
    && apt-get update \
    && apt-get -y --no-install-recommends install ${version} \
    && rm -rf /var/lib/apt/lists/*

CMD ["jshell"]

'''



def process_release(release, prefix, tags, git_dir):
    version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])
    tag_name = str.format('{0}-{1}', prefix, version_part)
    skip_tag = False
    dockerfile_dir = join(git_dir, 'dockerfiles', 'official', prefix)

    for tag in tags:
        if tag['name'] == tag_name:
            print(str.format('tag "{0}" already exists for release "{1}"', tag_name, release['name']))
            skip_tag = True
            break

    if not skip_tag:
        dockerfile_path = join(dockerfile_dir, 'Dockerfile')

        with open(dockerfile_path, 'w+') as dockerfile:
            dockerfile.write(Template(dockerfile_template).substitute(version=str.format('sapmachine-{0}-jdk={1}', major, version_part)))

        utils.git_commit(git_dir, 'updated Dockerfile', [dockerfile_path])
        utils.git_tag(git_dir, tag_name)
        utils.git_push(git_dir)
        utils.git_push_tag(git_dir, tag_name)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='specify the working directory', metavar='DIR', default='docker_work' ,required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    git_dir = join(workdir, 'sapmachine-infrastructure')

    utils.remove_if_exists(workdir)
    os.makedirs(workdir)

    releases = github_api_request('releases', per_page=100)
    infrastructure_tags = github_api_request('tags', repository='SapMachine-infrastructure', per_page=100)
    lts_release = None
    lts_release_major = 0
    stable_release = None

    for release in releases:
        if release['prerelease']:
            continue

        version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(release['name'])

        if utils.sapmachine_is_lts(major) and not lts_release:
            lts_release = release
            lts_release_major = major
        else:
            if not stable_release and major > lts_release_major:
                stable_release = release

        if lts_release and stable_release:
            break

    if lts_release or stable_release:
        utils.git_clone('github.com/SAP/SapMachine-infrastructure', 'master', git_dir)

    if lts_release and not stable_release:
        stable_release = lts_release

    if lts_release:
        print(str.format('found latest LTS release "{0}"', lts_release['name']))
        process_release(lts_release, 'lts', infrastructure_tags, git_dir)

    if stable_release:
        print(str.format('found latest stable release "{0}"', stable_release['name']))
        process_release(stable_release, 'stable', infrastructure_tags, git_dir)

    utils.remove_if_exists(workdir)

    return 0

if __name__ == "__main__":
    sys.exit(main())