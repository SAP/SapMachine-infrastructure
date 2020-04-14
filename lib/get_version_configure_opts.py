'''
Copyright (c) 2001-2020 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import utils
import argparse

VERSION_BUILD_ARG =         '--with-version-build={0}'
VERSION_PRE_ARG =           '--with-version-pre=ea'
VERSION_OPT_ARG =           '--with-version-opt={0}'
VENDOR_VERSION_STRING_ARG = '--with-vendor-version-string=SapMachine'
VERSION_EXTRA_ARG =         '--with-version-extra1={0}'

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine Git tag', metavar='TAG', required=True)
    parser.add_argument('-p', '--prerelease', help='this is a pre-release', action='store_true', default=False)
    args = parser.parse_args()

    tag = args.tag
    is_pre_release = args.prerelease
    version, version_part, major, update, version_sap, build_number, os_ext = utils.sapmachine_tag_components(tag)

    is_lts = utils.sapmachine_is_lts(major)
    major = int(major)
    update = int(update)

    version_build_opt = ''

    if 'BUILD_NUMBER' in os.environ:
        version_build_opt = VERSION_BUILD_ARG.format(os.environ['BUILD_NUMBER'])
    elif build_number is not None:
        version_build_opt = VERSION_BUILD_ARG.format(build_number)

    version_pre_opt = ''

    if is_pre_release:
        version_pre_opt = VERSION_PRE_ARG

    version_opt = ''

    if is_lts and not is_pre_release:
        if major < 15:
            version_opt = VERSION_OPT_ARG.format('LTS-sapmachine')
        else:
            version_opt = VERSION_OPT_ARG.format('LTS')
    else:
        if major < 15:
            version_opt = VERSION_OPT_ARG.format('sapmachine')

    vendor_version_string_opt = ''

    if (major > 14) or (major is 14 and update > 1) or (major is 11 and update > 7):
        vendor_version_string_opt = VENDOR_VERSION_STRING_ARG

    version_extra_opt = ''

    if version_sap is not None:
        version_extra_opt = VERSION_EXTRA_ARG.format(version_sap)

    configure_opts = ' '.join([
        version_build_opt,
        version_pre_opt,
        version_opt,
        vendor_version_string_opt,
        version_extra_opt
    ])

    print(configure_opts)

if __name__ == "__main__":
    sys.exit(main())
