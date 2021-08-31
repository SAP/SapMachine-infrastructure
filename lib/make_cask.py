'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import re
import sys
import utils
import versions

from os.path import join
from string import Template
from versions import SapMachineTag

release_cask_template = '''
cask 'sapmachine${MAJOR}-${IMAGE_TYPE}' do
  version '${VERSION}'
  sha256 '${SHA256}'

  url "https://github.com/SAP/SapMachine/releases/download/sapmachine-#{version}/sapmachine-${IMAGE_TYPE}-#{version}_${OS_NAME}-x64_bin.dmg"
  appcast "https://sap.github.io/SapMachine/latest/#{version.major}"
  name 'SapMachine OpenJDK Development Kit'
  homepage 'https://sapmachine.io/'

  artifact "sapmachine-${IMAGE_TYPE}-#{version}.${IMAGE_TYPE}", target: "/Library/Java/JavaVirtualMachines/sapmachine-#{version.major}.${IMAGE_TYPE}"

  uninstall rmdir: '/Library/Java/JavaVirtualMachines'
end
'''

pre_release_cask_template = '''
cask 'sapmachine${MAJOR}-ea-${IMAGE_TYPE}' do
  version '${VERSION},${BUILD_NUMBER}'
  sha256 '${SHA256}'

  url "https://github.com/SAP/SapMachine/releases/download/sapmachine-#{version.before_comma}%2B#{version.after_comma}/sapmachine-${IMAGE_TYPE}-#{version.before_comma}-ea.#{version.after_comma}_${OS_NAME}-x64_bin.dmg"
  appcast "https://sap.github.io/SapMachine/latest/#{version.major}"
  name 'SapMachine OpenJDK Development Kit'
  homepage 'https://sapmachine.io/'

  artifact "sapmachine-${IMAGE_TYPE}-#{version.before_comma}.${IMAGE_TYPE}", target: "/Library/Java/JavaVirtualMachines/sapmachine-#{version.major}-ea.${IMAGE_TYPE}"

  uninstall rmdir: '/Library/Java/JavaVirtualMachines'
end
'''

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='TAG', required=True)
    parser.add_argument('--sha256sum', help='the sha256 sum of the x86_64 dmg', metavar='SHA256', required=True)
    parser.add_argument('--aarchsha256sum', help='the sha256 sum of the aarch64 dmg', metavar='AARCHSHA256', required=False)
    parser.add_argument('-i', '--imagetype', help='The image type', metavar='IMAGETYPE', choices=['jdk', 'jre'])
    parser.add_argument('-p', '--prerelease', help='this is a pre-release', action='store_true', default=False)
    args = parser.parse_args()

    work_dir = join(os.getcwd(), 'cask_work')
    utils.remove_if_exists(work_dir)
    os.makedirs(work_dir)

    cask_version_pattern = re.compile('version \'((\d+\.?)+)(,(\d+))?\'')

    sapMachineTag = SapMachineTag.from_string(args.tag)
    if sapMachineTag is None:
        print(str.format("Tag {0} seems to be invalid. Aborting...", args.tag))
        sys.exit()

    if args.prerelease:
        if sapMachineTag.get_build_number() is None:
            print('No build number given for pre-release. Aborting ...')
            sys.exit()

        cask_content = Template(pre_release_cask_template).substitute(
            MAJOR=sapMachineTag.get_major(),
            VERSION=sapMachineTag.get_version_string_without_build(),
            BUILD_NUMBER=sapMachineTag.get_build_number(),
            IMAGE_TYPE=args.imagetype,
            OS_NAME='osx' if sapMachineTag.get_major() < 17 or (sapMachineTag.get_major() == 17 and sapMachineTag.get_build_number() < 21) else 'macos',
            SHA256=args.sha256sum
        )
        cask_file_name = str.format('sapmachine{0}-ea-{1}.rb', sapMachineTag.get_major(), args.imagetype)
    else:
        cask_content = Template(release_cask_template).substitute(
            MAJOR=sapMachineTag.get_major(),
            VERSION=sapMachineTag.get_version_string_without_build(),
            IMAGE_TYPE=args.imagetype,
            OS_NAME='osx' if sapMachineTag.get_major() < 17 else 'macos',
            SHA256=args.sha256sum
        )
        cask_file_name = str.format('sapmachine{0}-{1}.rb', sapMachineTag.get_major(), args.imagetype)

    homebrew_dir = join(work_dir, 'homebrew')
    cask_dir = join(homebrew_dir, 'Casks')
    cask_file_path = join(cask_dir, cask_file_name)

    utils.git_clone('github.com/SAP/homebrew-SapMachine', 'master', homebrew_dir)

    current_cask_version = None
    current_cask_build_number = None

    if os.path.exists(cask_file_path):
        with open(cask_file_path, 'r') as cask_file:
            cask_version_match = cask_version_pattern.search(cask_file.read())

            if cask_version_match is not None:
                if len(cask_version_match.groups()) >= 1:
                    current_cask_version = cask_version_match.group(1)
                if len(cask_version_match.groups()) >= 4:
                    current_cask_build_number = cask_version_match.group(4)

    current_cask_version = versions.version_to_tuple(current_cask_version, current_cask_build_number)

    if current_cask_version is None or sapMachineTag.get_version_tuple() >= current_cask_version:
        print(str.format("Creating/updating cask for version {0}...", sapMachineTag.get_version_tuple()))
        with open(cask_file_path, 'w') as cask_file:
            cask_file.write(cask_content)

        utils.git_commit(homebrew_dir, str.format('Update {0} ({1}).', cask_file_name, sapMachineTag.get_version_string()), [join('Casks', cask_file_name)])
        utils.git_push(homebrew_dir)
    else:
        print(str.format("Current cask has version {0} which is higher than {1}, no update.", current_cask_version, sapMachineTag.get_version_tuple()))

    return 0

if __name__ == "__main__":
    sys.exit(main())
