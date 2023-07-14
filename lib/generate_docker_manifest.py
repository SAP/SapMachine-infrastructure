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

dockerfile_version_pattern = re.compile('sapmachine-(\d+)-(jdk|jre)(-headless)?=(\S+)')

def fill_image_template(git_dir, dockerfiles_subdir, major, dockerpath, dockertag, isLatest, isLatestLts):
    dockerfile_path = join(dockerfiles_subdir, major, dockerpath, 'Dockerfile')
    with open(join(git_dir, dockerfile_path), 'r') as dockerfile:
        version_match = dockerfile_version_pattern.search(dockerfile.read())
    version = version_match.group(4)
    _, git_commit, _ = utils.run_cmd(['git', 'log', '-n', '1', '--pretty=format:%H', '--', dockerfile_path], cwd=git_dir, std=True)
    tags = [str.format('{0}-{1}', dockertag, major)]
    if major != version:
        tags.append(str.format('{0}-{1}', dockertag, version))
    if isLatestLts:
        tags.append(str.format('{0}-lts', dockertag))
    if dockertag == 'jdk-ubuntu':
        tags.append(major)
        if major != version:
            tags.append(version)
        if isLatest:
            tags.append('latest')
        if isLatestLts:
            tags.append('lts')

    return Template(template_image).substitute(tags=", ".join(tags), git_commit=git_commit, directory=str.format('{0}/{1}/{2}', dockerfiles_subdir, major, dockerpath))

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

    for _, dirs, _ in os.walk(join(git_dir, dockerfiles_subdir), topdown=False):
        for dir in dirs:
            if re.match(r"\d\d\d?", dir):
                releases.append(dir)
                if int(dir) > int(latest):
                    latest = dir
                if utils.sapmachine_is_lts(dir) and int(dir) > int(latest_lts):
                    latest_lts = dir

    releases.sort()

    images = []

    for release in releases:
        isLatest = release == latest
        isLatestLts = release == latest_lts

        images.append(fill_image_template(git_dir, dockerfiles_subdir, release, 'ubuntu/jre-headless', 'jre-headless-ubuntu', isLatest, isLatestLts))
        images.append(fill_image_template(git_dir, dockerfiles_subdir, release, 'ubuntu/jre', 'jre-ubuntu', isLatest, isLatestLts))
        images.append(fill_image_template(git_dir, dockerfiles_subdir, release, 'ubuntu/jdk-headless', 'jdk-headless-ubuntu', isLatest, isLatestLts))
        images.append(fill_image_template(git_dir, dockerfiles_subdir, release, 'ubuntu/jdk', 'jdk-ubuntu', isLatest, isLatestLts))

    with open(manifest, 'w') as manifest_file:
        manifest_file.write(Template(template_manifest).substitute(images='\n\n'.join(images)))

    return 0

if __name__ == "__main__":
    sys.exit(main())
