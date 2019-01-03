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

template_manifest = '''Maintainers: Rene Schuenemann <sapmachine@sap.com>
GitRepo: https://github.com/SAP/SapMachine-infrastructure.git

${images}
'''

template_image = '''Tags: ${tags}
Architectures: amd64
GitCommit: ${git_commit}
Directory: ${directory}'''

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', help='the directory containing the Dockerfiles', metavar='DIR', required=True)
    parser.add_argument('-m', '--manifest', help='the manifest file output directory and file name', metavar='FILE', required=True)
    parser.add_argument('--latest', help='the version major used as latest', metavar='MAJOR', required=False)
    args = parser.parse_args()

    dockerfiles_dir = args.directory
    latest_major = args.latest
    manifest = args.manifest

    images = ''

    for root, dirs, files in os.walk(dockerfiles_dir, topdown=False):
        for dir in dirs:
            directory = join(root, dir)
            major = dir
            retcode, git_commit, err = utils.run_cmd(['git', 'log', '-n', '1', '--pretty=format:%H', '--', join(directory, 'Dockerfile')], std=True)
            tags = major

            if latest_major == major:
                tags += str.format(', latest')

            if images:
                images += '\n\n'

            images += Template(template_image).substitute(tags=tags, git_commit=git_commit, directory=directory)

    with open(manifest, 'w') as manifest_file:
        manifest_file.write(Template(template_manifest).substitute(images=images))

if __name__ == "__main__":
    sys.exit(main())

