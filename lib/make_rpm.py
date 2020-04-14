'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import argparse
import utils
import glob
import shutil

from os import remove
from os import mkdir
from os import chdir
from os import listdir

from os.path import join
from os.path import realpath
from os.path import dirname
from os.path import basename
from os.path import exists
from os.path import isfile

from shutil import rmtree
from shutil import copytree
from shutil import move
from shutil import copy

from string import Template

spec_template = '''
Name:       sapmachine-jdk
Version:    ${version}
Release:    1
Summary:    The SapMachine JDK
Group:      Development/Languages/Java
License:    GPL-2.0-with-classpath-exception
BuildArch:  x86_64

AutoReqProv:    yes
Requires:       ca-certificates
Requires(post): /usr/sbin/alternatives

Provides: java-${major}
Provides: java-devel-${major}
Provides: java-sdk-${major}

%description
The SapMachine Java Development Kit
https://sapmachine.io

%install
mkdir -p %{buildroot}/usr/lib/jvm/sapmachine-${major}
cp -r ${workdir}/sapmachine-jdk-${version}/* %{buildroot}/usr/lib/jvm/sapmachine-${major}
find %{buildroot} -type f \( -name '*.so' -o -name '*.so.*' \) -exec chmod 755 {} +

%files
/usr/lib/jvm/sapmachine-${major}

%post
${alternatives}
'''

alternatives_template = 'update-alternatives --install /usr/bin/${tool} ${tool} /usr/lib/jvm/sapmachine-${major}/bin/${tool} 100'

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the tag to create the debian packages from', metavar='TAG', required=True)
    args = parser.parse_args()

    tag = args.tag

    cwd = os.getcwd()
    work_dir = join(cwd, 'rpm_work')
    version, version_part, major, update, version_sap, build_number, os_ext = utils.sapmachine_tag_components(tag)
    version = version.replace('-', '.')
    jdk_name = str.format('sapmachine-jdk-{0}', version)

    jdk_url, jre_url = utils.get_asset_url(tag, 'linux-x64')

    utils.remove_if_exists(work_dir)
    mkdir(work_dir)

    jdk_archive = join(work_dir, jdk_url.rsplit('/', 1)[-1])

    utils.download_artifact(jdk_url, jdk_archive)
    utils.extract_archive(jdk_archive, work_dir)

    bin_dir = join(work_dir, jdk_name, 'bin')
    tools = [f for f in listdir(bin_dir) if isfile(join(bin_dir, f))]
    alternatives = []
    alternatives_t = Template(alternatives_template)

    for tool in tools:
        alternatives.append(alternatives_t.substitute(tool=tool, major=major))

    alternatives = '\n'.join(alternatives)

    specfile_t = Template(spec_template)
    specfile_content = specfile_t.substitute(
        version=version,
        major=major,
        alternatives=alternatives,
        workdir=work_dir
    )

    with open(join(work_dir, 'sapmachine.spec'), 'w') as specfile:
        specfile.write(specfile_content)

    rpmbuild_dir = join(work_dir, 'rpmbuild')
    mkdir(rpmbuild_dir)

    rpmbuild_cmd = str.format('rpmbuild -bb -v --buildroot={0}/BUILD {0}/sapmachine.spec', work_dir)
    rpmbuild_cmd = rpmbuild_cmd.split(' ')
    rpmbuild_cmd.append('--define')
    rpmbuild_cmd.append(str.format('_rpmdir {0}', work_dir))
    rpmbuild_cmd.append('--define')
    rpmbuild_cmd.append(str.format('_topdir {0}', rpmbuild_dir))
    utils.run_cmd(rpmbuild_cmd, cwd=work_dir)

    rpm_files = glob.glob(join(work_dir, 'x86_64', '*.rpm'))

    for rpm_file in rpm_files:
        copy(rpm_file, cwd)
        remove(rpm_file)

    return 0

if __name__ == "__main__":
    sys.exit(main())