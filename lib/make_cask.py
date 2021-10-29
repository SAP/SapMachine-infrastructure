'''
Copyright (c) 2001-2021 by SAP SE, Walldorf, Germany.
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

duplex_cask_template = '''
cask 'sapmachine${CASK_TAG}-${IMAGE_TYPE}' do
  version '${CASK_VERSION}'

  if Hardware::CPU.intel?
    url "https://github.com/SAP/SapMachine/releases/download/sapmachine-${URL_VERSION1}/sapmachine-${IMAGE_TYPE}-${URL_VERSION2}_${OS_NAME}-x64_bin.dmg"
    sha256 '${INTELSHA256}'
  else
    url "https://github.com/SAP/SapMachine/releases/download/sapmachine-${URL_VERSION1}/sapmachine-${IMAGE_TYPE}-${URL_VERSION2}_${OS_NAME}-aarch64_bin.dmg"
    sha256 '${AARCHSHA256}'
  end

  appcast "https://sap.github.io/SapMachine/latest/#{version.major}"
  name 'SapMachine OpenJDK Development Kit'
  homepage 'https://sapmachine.io/'

  artifact "sapmachine-${IMAGE_TYPE}-#{${RUBY_VERSION}}.${IMAGE_TYPE}", target: "/Library/Java/JavaVirtualMachines/sapmachine-#{version.major}${EA_EXT}${IMAGE_TYPE}"

  uninstall rmdir: '/Library/Java/JavaVirtualMachines'
end
'''

cask_template = '''
cask 'sapmachine${CASK_TAG}-${IMAGE_TYPE}' do
  version '${CASK_VERSION}'
  sha256 '${SHA256}'

  url "https://github.com/SAP/SapMachine/releases/download/sapmachine-${URL_VERSION1}/sapmachine-${IMAGE_TYPE}-${URL_VERSION2}_${OS_NAME}-x64_bin.dmg"
  appcast "https://sap.github.io/SapMachine/latest/#{version.major}"
  name 'SapMachine OpenJDK Development Kit'
  homepage 'https://sapmachine.io/'

  artifact "sapmachine-${IMAGE_TYPE}-#{${RUBY_VERSION}}.${IMAGE_TYPE}", target: "/Library/Java/JavaVirtualMachines/sapmachine-#{version.major}${EA_EXT}${IMAGE_TYPE}"

  uninstall rmdir: '/Library/Java/JavaVirtualMachines'
end
'''


def replace_cask(cask_file_name, cask_content, sapMachineTag, homebrew_dir):
    cask_version_pattern = re.compile('version \'((\d+\.?)+)(,(\d+))?\'')
    current_cask_version = None
    current_cask_build_number = None
    cask_dir = join(homebrew_dir, 'Casks')
    cask_file_path = join(cask_dir, cask_file_name)

    if os.path.exists(cask_file_path):
        with open(cask_file_path, 'r') as cask_file:
            cask_version_match = cask_version_pattern.search(cask_file.read())

            if cask_version_match is not None:
                if len(cask_version_match.groups()) >= 1:
                    current_cask_version = cask_version_match.group(1)
                if len(cask_version_match.groups()) >= 4:
                    current_cask_build_number = cask_version_match.group(4)

    current_cask_version = versions.version_to_tuple(current_cask_version, current_cask_build_number)

    if current_cask_version is None or sapMachineTag.get_version_tuple() > current_cask_version:
        print(str.format("Creating/updating cask for version {0}...", sapMachineTag.get_version_tuple()))
        with open(cask_file_path, 'w') as cask_file:
            cask_file.write(cask_content)

        utils.git_commit(homebrew_dir, str.format('Update {0} ({1}).', cask_file_name, sapMachineTag.get_version_string()), [join('Casks', cask_file_name)])
        return True
    else:
        print(str.format("Current cask has version {0} which is not lower than {1}, no update.", current_cask_version, sapMachineTag.get_version_tuple()))
        return False

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='TAG', required=True)
    parser.add_argument('-d', '--dual', help='this is going to be a dual architecture cask (x64 and aarch64)', action='store_true', default=False)
    args = parser.parse_args()

    work_dir = join(os.getcwd(), 'cask_work')
    utils.remove_if_exists(work_dir)
    os.makedirs(work_dir)

    raw_tag = args.tag
    sapMachineTag = SapMachineTag.from_string(raw_tag)
    if sapMachineTag is None:
        print(str.format("Tag {0} seems to be invalid. Aborting...", args.tag))
        sys.exit(1)

    os_name = 'osx' if sapMachineTag.get_major() < 17 or (sapMachineTag.get_major() == 17 and sapMachineTag.get_update() is None and sapMachineTag.get_build_number() < 21) else 'macos'
    prerelease = not sapMachineTag.is_ga()
    if prerelease:
        jdk_cask_file_name = str.format('sapmachine{0}-ea-jdk.rb', sapMachineTag.get_major())
        jre_cask_file_name = str.format('sapmachine{0}-ea-jre.rb', sapMachineTag.get_major())
        cask_tag = str.format('{0}-ea', sapMachineTag.get_major())
        cask_version = str.format('{0},{1}', sapMachineTag.get_version_string_without_build(), sapMachineTag.get_build_number())
        ruby_version = 'version.before_comma'
        ea_ext = '-ea.'
        url_version1 = '#{version.before_comma}%2B#{version.after_comma}'
        url_version2 = '#{version.before_comma}-ea.#{version.after_comma}'
    else:
        jdk_cask_file_name = str.format('sapmachine{0}-jdk.rb', sapMachineTag.get_major())
        jre_cask_file_name = str.format('sapmachine{0}-jre.rb', sapMachineTag.get_major())
        cask_tag = str.format('{0}', sapMachineTag.get_major())
        cask_version = str.format('{0}', sapMachineTag.get_version_string_without_build())
        ruby_version = 'version'
        ea_ext = '.'
        url_version1 = '#{version}'
        url_version2 = '#{version}'

    if args.dual:
        try:
            aarch_jdk_sha_url, aarch_jre_sha_url = utils.get_asset_url(raw_tag, os_name + '-aarch64', '.sha256.dmg.txt')
            intel_jdk_sha_url, intel_jre_sha_url = utils.get_asset_url(raw_tag, os_name + '-x64', '.sha256.dmg.txt')
        except Exception as e:
            print('Not both platforms ready yet')
            sys.exit(0)

        aarch_jdk_sha, code1 = utils.download_asset(aarch_jdk_sha_url)
        aarch_jre_sha, code2 = utils.download_asset(aarch_jre_sha_url)
        intel_jdk_sha, code3 = utils.download_asset(intel_jdk_sha_url)
        intel_jre_sha, code4 = utils.download_asset(intel_jre_sha_url)
        if code1 != 200 or code2 != 200 or code3 != 200 or code4 != 200:
            print('Download failed')
            sys.exit(1)
        aarch_jdk_sha = aarch_jdk_sha.split(' ')[0]
        aarch_jre_sha = aarch_jre_sha.split(' ')[0]
        intel_jdk_sha = intel_jdk_sha.split(' ')[0]
        intel_jre_sha = intel_jre_sha.split(' ')[0]

        jdk_cask_content = Template(duplex_cask_template).substitute(
                CASK_TAG=cask_tag,
                IMAGE_TYPE='jdk',
                CASK_VERSION=cask_version,
                URL_VERSION1=url_version1,
                URL_VERSION2=url_version2,
                OS_NAME = os_name,
                INTELSHA256=intel_jdk_sha,
                AARCHSHA256=aarch_jdk_sha,
                RUBY_VERSION=ruby_version,
                EA_EXT=ea_ext
        )

        jre_cask_content = Template(duplex_cask_template).substitute(
                CASK_TAG=cask_tag,
                IMAGE_TYPE='jre',
                CASK_VERSION=cask_version,
                URL_VERSION1=url_version1,
                URL_VERSION2=url_version2,
                OS_NAME = os_name,
                INTELSHA256=intel_jre_sha,
                AARCHSHA256=aarch_jre_sha,
                RUBY_VERSION=ruby_version,
                EA_EXT=ea_ext
        )
    else:
        try:
            intel_jdk_sha_url, intel_jre_sha_url = utils.get_asset_url(raw_tag, os_name + '-x64', '.sha256.dmg.txt')
        except Exception as e:
            print('Asset not found3')
            sys.exit(1)

        intel_jdk_sha, code1 = utils.download_asset(intel_jdk_sha_url)
        intel_jre_sha, code2 = utils.download_asset(intel_jre_sha_url)
        if code1 != 200 or code2 != 200:
            print('Download failed')
            sys.exit(1)
        intel_jdk_sha = intel_jdk_sha.split(' ')[0]
        intel_jre_sha = intel_jre_sha.split(' ')[0]
        try:
            intel_jdk_url, intel_jre_url = utils.get_asset_url(raw_tag, os_name + '-x64', '.dmg')
        except Exception as e:
            print('Asset not found4')
            sys.exit(1)

        jdk_cask_content = Template(cask_template).substitute(
                CASK_TAG=cask_tag,
                IMAGE_TYPE='jdk',
                CASK_VERSION=cask_version,
                SHA256=intel_jdk_sha,
                URL_VERSION1=url_version1,
                URL_VERSION2=url_version2,
                OS_NAME = os_name,
                RUBY_VERSION=ruby_version,
                EA_EXT=ea_ext
        )

        jre_cask_content = Template(cask_template).substitute(
                CASK_TAG=cask_tag,
                IMAGE_TYPE='jre',
                CASK_VERSION=cask_version,
                SHA256=intel_jre_sha,
                URL_VERSION1=url_version1,
                URL_VERSION2=url_version2,
                OS_NAME = os_name,
                RUBY_VERSION=ruby_version,
                EA_EXT=ea_ext
        )

    homebrew_dir = join(work_dir, 'homebrew')
    utils.git_clone('github.com/SAP/homebrew-SapMachine', 'master', homebrew_dir)

    jdk_replaced = replace_cask(jdk_cask_file_name, jdk_cask_content, sapMachineTag, homebrew_dir)
    jre_replaced = replace_cask(jre_cask_file_name, jre_cask_content, sapMachineTag, homebrew_dir)
    if jdk_replaced or jre_replaced:
        utils.git_push(homebrew_dir)
    utils.remove_if_exists(work_dir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
