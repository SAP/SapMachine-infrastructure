'''
Copyright (c) 2001-2020 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import utils
import argparse
from datetime import date

VERSION_DATE_ARG =          '--with-version-date={0}'
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
    print(str.format("Info from tag {0}, {1}, {2}, {3}, {4}, {5}, {6}", version, version_part, major, update, version_sap, build_number, os_ext), file=sys.stderr)
    is_lts = utils.sapmachine_is_lts(major)
    major = int(major)
    update = int(update)

    configure_opts = []

    release_date = date.today().strftime("%Y-%m-%d")
    print(str.format("Today: {0}", release_date), file=sys.stderr)
    releases = utils.github_api_request('releases', per_page=100)
    if releases is not None:
        for release in releases:
            if release['tag_name'] == tag:
                release_date = release['published_at'].split('T')[0]
                print(str.format("Set release date from tag: {0}", release_date), file=sys.stderr)

    configure_opts.append(VERSION_DATE_ARG.format(release_date))

    if os.environ['BUILD_NUMBER']:
        configure_opts.append(VERSION_BUILD_ARG.format(os.environ['BUILD_NUMBER']))
        print(str.format("Set build id from environment: {0}", os.environ['BUILD_NUMBER']), file=sys.stderr)
    elif build_number is not None:
        configure_opts.append(VERSION_BUILD_ARG.format(build_number))
        print(str.format("Set build id from calculated build number: {0}", build_number), file=sys.stderr)

    if is_pre_release:
        configure_opts.append(VERSION_PRE_ARG)

    if is_lts and not is_pre_release:
        if major < 15:
            configure_opts.append(VERSION_OPT_ARG.format('LTS-sapmachine'))
        else:
            configure_opts.append(VERSION_OPT_ARG.format('LTS'))
    else:
        if major < 15:
            configure_opts.append(VERSION_OPT_ARG.format('sapmachine'))

    if (major > 14) or (major is 14 and update > 1) or (major is 11 and update > 7):
        configure_opts.append(VENDOR_VERSION_STRING_ARG)

    if version_sap is not None:
        configure_opts.append(VERSION_EXTRA_ARG.format(version_sap))

    print(' '.join(configure_opts))

if __name__ == "__main__":
    sys.exit(main())
