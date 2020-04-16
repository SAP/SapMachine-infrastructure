'''
Copyright (c) 2001-2020 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import utils
import argparse
from datetime import date
from versions import SapMachineTag

VERSION_DATE_ARG =          '--with-version-date={0}'
VERSION_BUILD_ARG =         '--with-version-build={0}'
VERSION_PRE_ARG =           '--with-version-pre={0}'
VERSION_OPT_ARG =           '--with-version-opt={0}'
VERSION_EXTRA1_ARG =        '--with-version-extra1={0}'
VENDOR_VERSION_STRING_ARG = '--with-vendor-version-string=SapMachine'
VENDOR_NAME_ARG =           '--with-vendor-name="SAP SE"'
VENDOR_URL_ARG =            '--with-vendor-url=https://sapmachine.io/'
VENDOR_BUG_URL_ARG =        '--with-vendor-bug-url=https://github.com/SAP/SapMachine/issues/new'
VENDOR_VM_BUG_URL_ARG =     '--with-vendor-vm-bug-url=https://github.com/SAP/SapMachine/issues/new'

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine git tag', metavar='TAG')
    parser.add_argument('-b', '--build', help='the build number to use, overrules any value from tag(s)', metavar='BUILD_NR')
    parser.add_argument('-r', '--release', help='set if this is a release build', action='store_true', default=False)
    args = parser.parse_args()

    configure_opts = []

    # parse tag, if given
    tag = None
    if args.tag:
        tag = SapMachineTag.from_string(args.tag)
        if tag is None:
            print(str.format("Passed tag {0} not recognized as SapMachine tag, handling as snapshot build", args.tag), file=sys.stderr)

    # determine and set version date
    release_date = None
    if tag is not None:
        releases = utils.get_github_releases()
        if releases is not None:
            for release in releases:
                if release['tag_name'] == tag.as_string():
                    release_date = release['published_at'].split('T')[0]
                    print(str.format("Set date to release date of {0}: {1}", tag.as_string(), release_date), file=sys.stderr)
                    break
        if release_date is None:
            print(str.format("Tag {0} does not seem to exist or data could not be loaded from GitHub", tag.as_string()), file=sys.stderr)

    if release_date is None:
        release_date = date.today().strftime("%Y-%m-%d")
        print(str.format("Set date to today: {0}", release_date), file=sys.stderr)

    configure_opts.append(VERSION_DATE_ARG.format(release_date))

    # determine and set build number
    build_number = None
    if args.build is not None:
        build_number = args.build
        print(str.format("Set build number from parameter: {0}", build_number), file=sys.stderr)

    if build_number is None and tag is not None:
        build_number = tag.get_build_number()
        if build_number is not None:
            print(str.format("Set build number from tag: {0}", build_number), file=sys.stderr)
        else:
            latest_non_ga_tag = tag.get_latest_non_ga_tag()
            if latest_non_ga_tag is not None:
                build_number = latest_non_ga_tag.get_build_number()
                if build_number is not None:
                    print(str.format("Tag seems to be a ga tag, using build number from latest non-ga tag {0}: {1}",
                        latest_non_ga_tag.as_string(), build_number), file=sys.stderr)

    if build_number is not None:
        configure_opts.append(VERSION_BUILD_ARG.format(build_number))

    # set version pre
    if not args.release:
        if tag is None:
            configure_opts.append(VERSION_PRE_ARG.format('snapshot'))
        else:
            configure_opts.append(VERSION_PRE_ARG.format('ea'))
    else:
        configure_opts.append(VERSION_PRE_ARG.format(''))

    # set version opt
    if tag is None:
        configure_opts.append(VERSION_OPT_ARG.format(release_date))
    else:
        if args.release and utils.sapmachine_is_lts(tag.get_major()):
            if tag.get_major() < 15:
                configure_opts.append(VERSION_OPT_ARG.format('LTS-sapmachine'))
            else:
                configure_opts.append(VERSION_OPT_ARG.format('LTS'))
        else:
            if tag.get_major() < 15:
                configure_opts.append(VERSION_OPT_ARG.format('sapmachine'))
            else:
                configure_opts.append(VERSION_OPT_ARG.format(''))

    # set version extra1 arg (= sap version)
    if tag is not None and tag.get_version_sap() is not None:
        configure_opts.append(VERSION_EXTRA1_ARG.format(tag.get_version_sap()))

    # set vendor version string
    if (tag is None or
        (tag.get_major() > 14) or
        (tag.get_major() == 14 and tag.get_update() > 1) or
        (tag.get_major() == 11 and tag.get_update() > 7)):
        configure_opts.append(VENDOR_VERSION_STRING_ARG)

    # set other vendor options
    configure_opts.append(VENDOR_NAME_ARG)
    configure_opts.append(VENDOR_URL_ARG)
    configure_opts.append(VENDOR_BUG_URL_ARG)
    configure_opts.append(VENDOR_VM_BUG_URL_ARG)

    print(' '.join(configure_opts))

    return 0

if __name__ == "__main__":
    sys.exit(main())
