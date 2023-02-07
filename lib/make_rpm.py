'''
Copyright (c) 2017-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import glob
import os
import re
import sys
import utils

from os import listdir
from os import mkdir
from os import remove
from os.path import isfile
from os.path import join
from shutil import copy
from string import Template
from versions import SapMachineTag

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

%define _source_payload w7.xzdio
%define _binary_payload w7.xzdio

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
    parser.add_argument('-t', '--tag', help='SapMachine version tag to create the rpm package for', metavar='TAG')
    parser.add_argument('-d', '--download', help='Download artifact and clone git repo', action='store_true')
    parser.add_argument('-a', '--architecture', help='specifies the architecture (linux-aarch64, linux-ppc64le, linux-x64)', metavar='ARCH', default='linux-x64')
    args = parser.parse_args()

    cwd = os.getcwd()
    work_dir = join(cwd, 'rpm_work')
    utils.remove_if_exists(work_dir)
    mkdir(work_dir)

    if not args.download:
        bundle_name_file = join(cwd, 'jdk_bundle_name.txt')
        if not isfile(bundle_name_file):
            print(str.format("Bundle name file \"{0}\" does not exist. I don't know what to package", bundle_name_file))
            return -1
        with open(bundle_name_file, 'r') as file:
            bundle_name = file.read().rstrip()
        print(str.format("Bundle Name: {0}", bundle_name))

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        if args.download:
            print(str.format("Passed tag \"{0}\" is invalid. I don't know what to download!", args.tag))
            return -1
        else:
            bundle_name_match = re.compile('sapmachine-\w+-((\d+)(\.\d+)*).*').match(bundle_name)
            major = bundle_name_match.group(2)
            version = bundle_name_match.group(1).replace('-', '.')
            jdk_name = str.format('sapmachine-{0}-jdk-{1}', major, version)
            jdk_url = "https://sapmachine.io"
    else:
        major = tag.get_major()
        version = tag.get_version_string().replace('-', '.')
        jdk_name = str.format('sapmachine-{0}-jdk-{1}', major, version)
        jdk_url = utils.get_asset_urls(tag, args.architecture, ["jdk"])['jdk']

    if args.download:
        src_dir = join(work_dir, 'sapmachine_master')
        utils.git_clone('github.com/SAP/SapMachine', args.tag, src_dir)
        jdk_archive = join(work_dir, jdk_url.rsplit('/', 1)[-1])
        utils.download_artifact(jdk_url, jdk_archive)
    else:
        src_dir = join(cwd, 'SapMachine')
        jdk_archive = join(cwd, bundle_name)

    utils.extract_archive(jdk_archive, work_dir)

    bin_dir = join(work_dir, jdk_name, 'bin')
    tools = [f for f in listdir(bin_dir) if isfile(join(bin_dir, f))]
    alternatives = []
    alternatives_t = Template(alternatives_template)

    for tool in tools:
        alternatives.append(alternatives_t.substitute(tool=tool, major=tag.get_major()))

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
