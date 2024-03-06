'''
Copyright (c) 2017-2024 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import utils
import versions

from os.path import join
from string import Template
from versions import SapMachineTag

cask_template = '''cask "sapmachine${CASK_TAG}-${IMAGE_TYPE}" do
  version "${CASK_VERSION}"
  arch arm: "aarch64", intel: "x64"
  sha256 arm:   "${AARCHSHA256}",
         intel: "${INTELSHA256}"

  url "https://github.com/SAP/SapMachine/releases/download/sapmachine-${URL_VERSION1}/sapmachine-${IMAGE_TYPE}-${URL_VERSION2}_macos-#{arch}_bin.dmg",
      verified: "github.com/SAP/SapMachine/"

  name "SapMachine OpenJDK Development Kit"
  desc "OpenJDK distribution from SAP"
  homepage "https://sapmachine.io/"

  # Check for latest version in SapMachine release data.
  livecheck do
    url "https://sap.github.io/SapMachine/assets/data/sapmachine-releases-latest.json"
    regex(/["']tag["']:\s*["']sapmachine[._-]v?(\d+(?:\.\d+)*)["']/i)
  end

  artifact "sapmachine-${IMAGE_TYPE}-#{${RUBY_VERSION}}.${IMAGE_TYPE}", target: "/Library/Java/JavaVirtualMachines/sapmachine-#{version.major}${EA_EXT}${IMAGE_TYPE}"
end
'''

def version_to_tuple(version_without_build_number, build_number):
    if version_without_build_number is not None:
        version = list(map(int, version_without_build_number.split('.')))
        version.extend([0 for i in range(5 - len(version))])
        version = tuple(version)
        version += (int(build_number),) if build_number is not None else (99999,)
        return version

    return None

def replace_cask(cask_file_name, cask_content, tag, homebrew_dir):
    cask_version_pattern = re.compile('version \"((\d+\.?)+)(,(\d+))?\"')
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

    current_cask_version = version_to_tuple(current_cask_version, current_cask_build_number)
    current_tag_version = version_to_tuple(tag.get_version_string_without_build(), tag.get_build_number())

    if current_cask_version is None or current_tag_version >= current_cask_version:
        print(str.format("Creating/updating cask with version {0}, old version was {1}...", current_tag_version, current_cask_version))
        with open(cask_file_path, 'w') as cask_file:
            cask_file.write(cask_content)

        utils.run_cmd("git add .".split(' '), cwd=homebrew_dir)
        _, diff, _  = utils.run_cmd("git diff HEAD".split(' '), cwd=homebrew_dir, std=True)
        if diff.strip():
            utils.git_commit(homebrew_dir, str.format('Update {0} ({1}).', cask_file_name, tag.get_version_string()), [join('Casks', cask_file_name)])
            return True
        else:
            print("No changes.")
            return False
    else:
        print(str.format("Current cask has version {0} which is higher than {1}, no update.", current_cask_version, current_tag_version))
        return False

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='TAG', required=True)
    args = parser.parse_args()

    work_dir = join(os.getcwd(), 'cask_work')
    utils.remove_if_exists(work_dir)
    os.makedirs(work_dir)

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        print(str.format("Tag {0} seems to be invalid. Aborting...", args.tag))
        sys.exit(1)

    prerelease = not tag.is_ga()
    if prerelease:
        jdk_cask_file_name = str.format('sapmachine{0}-ea-jdk.rb', tag.get_major())
        jre_cask_file_name = str.format('sapmachine{0}-ea-jre.rb', tag.get_major())
        cask_tag = str.format('{0}-ea', tag.get_major())
        cask_version = str.format('{0},{1}', tag.get_version_string_without_build(), tag.get_build_number())
        ruby_version = 'version.before_comma'
        ea_ext = '-ea.'
        url_version1 = '#{version.before_comma}%2B#{version.after_comma}'
        url_version2 = '#{version.before_comma}-ea.#{version.after_comma}'
    else:
        jdk_cask_file_name = str.format('sapmachine{0}-jdk.rb', tag.get_major())
        jre_cask_file_name = str.format('sapmachine{0}-jre.rb', tag.get_major())
        cask_tag = str.format('{0}', tag.get_major())
        cask_version = str.format('{0}', tag.get_version_string_without_build())
        ruby_version = 'version'
        ea_ext = '.'
        url_version1 = '#{version}'
        url_version2 = '#{version}'

    try:
        aarch_urls = utils.get_asset_urls(tag, 'macos-aarch64', pattern='.dmg.sha256.txt')
        intel_urls = utils.get_asset_urls(tag, 'macos-x64', pattern='.dmg.sha256.txt')
    except Exception as e:
        print(str.format('No assets found for tag {0}', tag.as_string()))
        sys.exit(1)

    if not "jdk" in aarch_urls and not "jdk" in intel_urls:
        print(str.format('No jdk assets found for tag {0}', tag.as_string()))
        sys.exit(1)

    if not "jdk" in aarch_urls or not "jdk" in intel_urls:
        print(str.format('Not all platforms ready yet, jdk missing for tag {0}', tag.as_string()))
        sys.exit(0)

    if not "jre" in aarch_urls and not "jre" in intel_urls:
        print(str.format('No jre assets found for tag {0}', tag.as_string()))
        sys.exit(1)

    if not "jre" in aarch_urls or not "jre" in intel_urls:
        print(str.format('Not all platforms ready yet, jre missing for tag {0}', tag.as_string()))
        sys.exit(0)

    aarch_jdk_sha = utils.download_text(aarch_urls["jdk"]).split(' ')[0]
    aarch_jre_sha = utils.download_text(aarch_urls["jre"]).split(' ')[0]
    intel_jdk_sha = utils.download_text(intel_urls["jdk"]).split(' ')[0]
    intel_jre_sha = utils.download_text(intel_urls["jre"]).split(' ')[0]

    jdk_cask_content = Template(cask_template).substitute(
            CASK_TAG = cask_tag,
            IMAGE_TYPE = 'jdk',
            CASK_VERSION = cask_version,
            URL_VERSION1 = url_version1,
            URL_VERSION2 = url_version2,
            INTELSHA256 = intel_jdk_sha,
            AARCHSHA256 = aarch_jdk_sha,
            RUBY_VERSION = ruby_version,
            EA_EXT = ea_ext
    )

    jre_cask_content = Template(cask_template).substitute(
            CASK_TAG = cask_tag,
            IMAGE_TYPE = 'jre',
            CASK_VERSION = cask_version,
            URL_VERSION1 = url_version1,
            URL_VERSION2 = url_version2,
            INTELSHA256 = intel_jre_sha,
            AARCHSHA256 = aarch_jre_sha,
            RUBY_VERSION = ruby_version,
            EA_EXT = ea_ext
    )

    homebrew_dir = join(work_dir, 'homebrew')
    utils.git_clone('github.com/SAP/homebrew-SapMachine', 'master', homebrew_dir)

    jdk_replaced = replace_cask(jdk_cask_file_name, jdk_cask_content, tag, homebrew_dir)
    jre_replaced = replace_cask(jre_cask_file_name, jre_cask_content, tag, homebrew_dir)
    if jdk_replaced or jre_replaced:
        utils.git_push(homebrew_dir)
    utils.remove_if_exists(work_dir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
