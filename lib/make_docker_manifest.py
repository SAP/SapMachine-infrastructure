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

template_manifest = '''Maintainers: Rene Schuenemann <sapmachine@sap.com> (@reshnm)
GitRepo: https://github.com/SAP/SapMachine-infrastructure.git

${images}
'''

template_image = '''Tags: ${tags}
Architectures: amd64
GitCommit: ${git_commit}
Directory: ${directory}'''

dockerfile_version_pattern = re.compile('sapmachine-(\d+)-jdk=(\S+)')

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', help='the directory containing the Dockerfiles', metavar='DIR', required=True)
    parser.add_argument('-m', '--manifest', help='the manifest file output directory and file name', metavar='FILE', required=True)
    args = parser.parse_args()

    dockerfiles_dir = args.directory
    manifest = args.manifest

    images = ''

    for root, dirs, files in os.walk(dockerfiles_dir, topdown=False):
        for dir in dirs:
            if dir == 'stable' or dir == 'lts':
                directory = join(root, dir)

                with open(join(directory, 'Dockerfile'), 'r') as dockerfile:
                    version_match = dockerfile_version_pattern.search(dockerfile.read())

                major = version_match.group(1)
                version = version_match.group(2)
                retcode, git_commit, err = utils.run_cmd(['git', 'log', '-n', '1', '--pretty=format:%H', '--', join(directory, 'Dockerfile')], std=True)
                tags = str.format('{0}, {1}, {2}', major, version, 'latest' if dir == 'stable' else 'lts')

                if images:
                    images += '\n\n'

                images += Template(template_image).substitute(tags=tags, git_commit=git_commit, directory=directory)

    with open(manifest, 'w') as manifest_file:
        manifest_file.write(Template(template_manifest).substitute(images=images))

if __name__ == "__main__":
    sys.exit(main())

