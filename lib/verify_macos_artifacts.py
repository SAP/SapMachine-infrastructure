'''
Copyright (c) 2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tarfile
#quick hack: import utils. Otherwise there is a circularity when importing SapMachineTag from versions.
import utils

from os.path import join
from versions import SapMachineTag

def test_platform(version, filename, suffix):
    if suffix == "tar.gz":
        dest_dir = join(os.getcwd(), 'destination')
        utils.remove_if_exists(dest_dir)
        file = tarfile.open(filename)
        file.extractall('./destination')
        p = glob.glob("./destination/*/Contents/Home/bin/java")
        if p:
            err = subprocess.run([p[0], "-version"], capture_output=True, text=True).stderr
            pattern = re.compile(r'openjdk (version ")?(?P<version>[\.\d]+)')
            print("java -version output:", err.replace('\n', '\\n'))
            m = pattern.match(err)
            assert m and m.group('version'), 'could not extract version from line: ' + err
            return 0
        else:
            return -1
    else:
        return -1

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', '-t', help='The SapMachine Git tag', metavar='TAG', required=True)
    parser.add_argument('--platform', '-p', help='The MacOS platform to be tested. Could be "x64" and/or "aarch64"', metavar='PLATFORM',  required=True)
    args = parser.parse_args()

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        print("Invalid tag: ", args.tag)
        return -1

    os_name = "macos" if tag.get_major() >= 17 or (tag.get_major() == 11 and tag.get_update() > 15) else "osx"
    jdk_tgz = "sapmachine-jdk-" + tag.get_version_string() + "_" + os_name + "-" + args.platform + "_bin.tar.gz"
    # jdk_dmg ="sapmachine-jdk-" + tag.get_version_string() + "_" + os_name + "-" + args.platform + "_bin.dmg"
    jre_tgz = "sapmachine-jre-" + tag.get_version_string() + "_" + os_name + "-" + args.platform + "_bin.tar.gz"
    # jre_dmg ="sapmachine-jre-" + tag.get_version_string() + "_" + os_name + "-" + args.platform + "_bin.dmg"

    if test_platform(tag.get_version_string(), jdk_tgz, "tar.gz") == 0:
        print("Successfully verified " + jdk_tgz)
    else:
        print("Error verifying " + jdk_tgz)
        return -1
    if test_platform(tag.get_version_string(), jre_tgz, "tar.gz") == 0:
        print("Successfully verified " + jre_tgz)
    else:
        print("Error verifying " + jre_tgz)
        return -1

    return 0

if __name__ == "__main__":
    sys.exit(main())
