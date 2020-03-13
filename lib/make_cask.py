'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import re
import utils
import argparse

from os.path import join
from string import Template

release_cask_template = '''
cask 'sapmachine${MAJOR}-${IMAGE_TYPE}' do
  version '${VERSION}'
  sha256 '${SHA256}'

  url "https://github.com/SAP/SapMachine/releases/download/sapmachine-#{version}/sapmachine-${IMAGE_TYPE}-#{version}_osx-x64_bin.dmg"
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

  url "https://github.com/SAP/SapMachine/releases/download/sapmachine-#{version.before_comma}%2B#{version.after_comma}/sapmachine-${IMAGE_TYPE}-#{version.before_comma}-ea.#{version.after_comma}_osx-x64_bin.dmg"
  appcast "https://sap.github.io/SapMachine/latest/#{version.major}"
  name 'SapMachine OpenJDK Development Kit'
  homepage 'https://sapmachine.io/'

  artifact "sapmachine-${IMAGE_TYPE}-#{version.before_comma}.${IMAGE_TYPE}", target: "/Library/Java/JavaVirtualMachines/sapmachine-#{version.major}-ea.${IMAGE_TYPE}"

  uninstall rmdir: '/Library/Java/JavaVirtualMachines'
end
'''

def version_to_tuple(version, build_number):
    if version is not None:
        version = list(map(int, version.split('.')))
        version.extend([0 for i in range(5 - len(version))])
        version = tuple(version)
        version += (int(build_number),) if build_number is not None else (99999,)
        return version

    return None

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='TAG', required=True)
    parser.add_argument('--sha256sum', help='the sha256 sum', metavar='SHA256', required=True)
    parser.add_argument('-i', '--imagetype', help='The image type', metavar='IMAGETYPE', choices=['jdk', 'jre'])
    parser.add_argument('-p', '--prerelease', help='this is a pre-release', action='store_true', default=False)
    args = parser.parse_args()

    cwd = os.getcwd()
    work_dir = join(cwd, 'cask_work')
    tag = args.tag
    sha256sum = args.sha256sum
    image_type = args.imagetype
    is_prerelease = args.prerelease

    cask_version_pattern = re.compile('version \'((\d+\.?)+)(,(\d+))?\'')

    utils.remove_if_exists(work_dir)
    os.makedirs(work_dir)

    version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(tag)

    if is_prerelease:
        if build_number is None:
            print('No build number given. Aborting ...')
            sys.exit()

        cask_content = Template(pre_release_cask_template).substitute(
            MAJOR=major,
            VERSION=version_part,
            BUILD_NUMBER=build_number,
            IMAGE_TYPE=image_type,
            SHA256=sha256sum
        )
        cask_file_name = str.format('sapmachine{0}-ea-{1}.rb', major, image_type)
    else:
        cask_content = Template(release_cask_template).substitute(
            MAJOR=major,
            VERSION=version_part,
            IMAGE_TYPE=image_type,
            SHA256=sha256sum
        )
        cask_file_name = str.format('sapmachine{0}-{1}.rb', major, image_type)

    homebrew_dir = join(work_dir, 'homebrew')
    cask_dir = join(homebrew_dir, 'Casks')
    utils.git_clone('github.com/SAP/homebrew-SapMachine', 'master', homebrew_dir)

    current_cask_version = None
    current_cask_build_number = None

    if os.path.exists(join(cask_dir, cask_file_name)):
        with open(join(cask_dir, cask_file_name), 'r') as cask_file:
            cask_version_match = cask_version_pattern.search(cask_file.read())

            if cask_version_match is not None:
                if len(cask_version_match.groups()) >= 1:
                    current_cask_version = cask_version_match.group(1)
                if len(cask_version_match.groups()) >= 4:
                    current_cask_build_number = cask_version_match.group(4)

    current_cask_version = version_to_tuple(current_cask_version, current_cask_build_number)
    new_cask_version = version_to_tuple(version_part, build_number)

    if new_cask_version >= current_cask_version:
        with open(join(cask_dir, cask_file_name), 'w') as cask_file:
            cask_file.write(cask_content)

        utils.git_commit(homebrew_dir, str.format('Updated {0}.', cask_file_name), [join('Casks', cask_file_name)])
        utils.git_push(homebrew_dir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
