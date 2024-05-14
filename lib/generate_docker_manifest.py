'''
Copyright (c) 2019-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import re
import sys
import utils

from os.path import join
from string import Template

template_manifest = '''Maintainers: Christoph Langer <sapmachine@sap.com> (@realclanger), Christian Halstrick <sapmachine@sap.com> (@chalstrick)
GitRepo: https://github.com/SAP/SapMachine-infrastructure.git

${images}
'''

template_image = '''Tags: ${tags}
Architectures: amd64, arm64v8, ppc64le
GitCommit: ${git_commit}
Directory: ${directory}'''

dockerfile_version_pattern_ubuntu = re.compile('sapmachine-(\d+)-(jdk|jre)(-headless)?=(\S+)')

def fill_image_template_ubuntu(git_dir, dockerfiles_subdir, major, ubuntu_ver, type, isLatest, isLatestLts):
    #dockerpath: 'ubuntu/jre-headless', dockertag: 'jre-headless-ubuntu'
    dockerfile_path = join(dockerfiles_subdir, major, 'ubuntu', f'{ubuntu_ver[0]}_{ubuntu_ver[1]}', type, 'Dockerfile')
    dockertag = f'{type}-ubuntu'
    with open(join(git_dir, dockerfile_path), 'r') as dockerfile:
        version_match = dockerfile_version_pattern_ubuntu.search(dockerfile.read())
    version = version_match.group(4)
    _, git_commit, _ = utils.run_cmd(['git', 'log', '-n', '1', '--pretty=format:%H', '--', dockerfile_path], cwd=git_dir, std=True)
    tags = []
    if ubuntu_ver[3] is True:
        if dockertag == 'jdk-ubuntu':
            if isLatest:
                tags.append('latest')
        if isLatest:
            tags.append(f'{dockertag}')
        if dockertag == 'jdk-ubuntu':
            tags.append(major)
            if isLatestLts:
                tags.append('lts')
        tags.append(f'{major}-{dockertag}')
        if isLatestLts:
            tags.append(f'lts-{dockertag}')
        if dockertag == 'jdk-ubuntu':
            if major != version:
                tags.append(version)
        if major != version:
            tags.append(f'{version}-{dockertag}')

    if dockertag == 'jdk-ubuntu':
        if isLatest:
            tags.append(f'ubuntu-{ubuntu_ver[2]}')
            tags.append(f'ubuntu-{ubuntu_ver[0]}.{ubuntu_ver[1]}')
        tags.append(f'{major}-ubuntu-{ubuntu_ver[2]}')
        tags.append(f'{major}-ubuntu-{ubuntu_ver[0]}.{ubuntu_ver[1]}')
        if isLatestLts:
            tags.append(f'lts-ubuntu-{ubuntu_ver[2]}')
            tags.append(f'lts-ubuntu-{ubuntu_ver[0]}.{ubuntu_ver[1]}')
        if major != version:
            tags.append(f'{version}-ubuntu-{ubuntu_ver[2]}')
            tags.append(f'{version}-ubuntu-{ubuntu_ver[0]}.{ubuntu_ver[1]}')
    tags.append(f'{major}-{dockertag}-{ubuntu_ver[2]}')
    tags.append(f'{major}-{dockertag}-{ubuntu_ver[0]}.{ubuntu_ver[1]}')
    if isLatest:
        tags.append(f'{dockertag}-{ubuntu_ver[2]}')
        tags.append(f'{dockertag}-{ubuntu_ver[0]}.{ubuntu_ver[1]}')
    if isLatestLts:
        tags.append(f'lts-{dockertag}-{ubuntu_ver[2]}')
        tags.append(f'lts-{dockertag}-{ubuntu_ver[0]}.{ubuntu_ver[1]}')
    if major != version:
        tags.append(f'{version}-{dockertag}-{ubuntu_ver[2]}')
        tags.append(f'{version}-{dockertag}-{ubuntu_ver[0]}.{ubuntu_ver[1]}')

    return Template(template_image).substitute(tags=", ".join(tags), git_commit=git_commit, directory=f'{dockerfiles_subdir}/{major}/ubuntu/{ubuntu_ver[0]}_{ubuntu_ver[1]}/{type}')

template_image_distroless = '''Tags: ${tags}
Architectures: amd64, arm64, ppc64le
GitCommit: ${git_commit}
Directory: ${directory}'''

dockerfile_version_pattern_distroless = re.compile('sapmachine-(\d+(?:\.\d+)*)')

def fill_image_template_distroless(git_dir, dockerfiles_subdir, major, dockerpath, dockertag, isLatest, isLatestLts):
    dockerfile_path = join(dockerfiles_subdir, major, dockerpath, 'Dockerfile')
    with open(join(git_dir, dockerfile_path), 'r') as dockerfile:
        version_match = dockerfile_version_pattern_distroless.search(dockerfile.read())
    version = version_match.group(1)
    _, git_commit, _ = utils.run_cmd(['git', 'log', '-n', '1', '--pretty=format:%H', '--', dockerfile_path], cwd=git_dir, std=True)
    tags = [str.format('{0}-{1}', dockertag, major)]
    if major != version:
        tags.append(str.format('{0}-{1}', dockertag, version))
    if isLatest:
        tags.append(str.format('{0}', dockertag))
    if isLatestLts:
        tags.append(str.format('{0}-lts', dockertag))
    if dockertag == 'jdk-distroless':
        tags.append(major)
        if major != version:
            tags.append(version)
        if isLatest:
            tags.append('latest')
        if isLatestLts:
            tags.append('lts')

    return Template(template_image_distroless).substitute(tags=", ".join(tags), git_commit=git_commit, directory=str.format('{0}/{1}/{2}', dockerfiles_subdir, major, dockerpath))

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default='dockerfiles/official', help='the subdirectory in the GitHub repository, containing the Dockerfiles', metavar='DIR')
    parser.add_argument('-m', '--manifest', default='sapmachine', help='the output manifest file (name and/or path)', metavar='FILE')
    args = parser.parse_args()

    dockerfiles_subdir = args.directory
    manifest = args.manifest
    git_dir = os.path.abspath(join(os.path.dirname(__file__), '..'))

    latest_lts = '00'
    latest = '00'
    releases = []

    for dir in os.listdir(join(git_dir, dockerfiles_subdir)):
        if re.match(r"\d\d\d?", dir):
            releases.append(dir)
            if int(dir) > int(latest):
                latest = dir
            if utils.sapmachine_is_lts(dir) and int(dir) > int(latest_lts):
                latest_lts = dir

    releases.sort(reverse=True)

    images = []
    image_types = ['jdk', 'jdk-headless', 'jre', 'jre-headless']

    for release in releases:
        isLatest = release == latest
        isLatestLts = release == latest_lts
        # Active releases as per https://ubuntu.com/about/release-cycle
        for ubuntu_ver in [('24', '04', 'noble', True),
                           ('22', '04', 'jammy', False),
                           ('20', '04', 'focal', False)]:
            for type in image_types:
                images.append(fill_image_template_ubuntu(git_dir, dockerfiles_subdir, release, ubuntu_ver, type, isLatest, isLatestLts))

        #images.append(fill_image_template_distroless(git_dir, dockerfiles_subdir, release, 'distroless/debian11/latest', 'distroless-debian11', isLatest, isLatestLts))
        #images.append(fill_image_template_distroless(git_dir, dockerfiles_subdir, release, 'distroless/debian11/nonroot', 'distroless-debian11-nonroot', isLatest, isLatestLts))
        #images.append(fill_image_template_distroless(git_dir, dockerfiles_subdir, release, 'distroless/debian11/debug', 'distroless-debian11-debug', isLatest, isLatestLts))
        #images.append(fill_image_template_distroless(git_dir, dockerfiles_subdir, release, 'distroless/debian11/debug-nonroot', 'distroless-debian11-debug-nonroot', isLatest, isLatestLts))

    with open(manifest, 'w') as manifest_file:
        manifest_file.write(Template(template_manifest).substitute(images='\n\n'.join(images)))

    return 0

if __name__ == "__main__":
    sys.exit(main())
