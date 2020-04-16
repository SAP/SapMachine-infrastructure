'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import sys
import utils
from os.path import join
from versions import Tag, SapMachineTag, JDKTag

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='Test a tag', metavar='TAG')
    parser.add_argument('-l', '--list-latest-non-ga', help='List the latest non-ga tag', action='store_true', default=False)
    parser.add_argument('-a', '--test-all-tags', nargs='?', default='not present', const='all', help='List the latest non-ga tag, value could be sap,jdk,unknown')
    parser.add_argument('-v', '--jvm', help='Test a VM', metavar='VM Path')
    args = parser.parse_args()

    if args.tag:
        tag = Tag.from_string(args.tag)
        if tag is None:
            print(str.format("Tag value {0} seems to be an invalid tag", args.tag))
            sys.exit(-1)
        tag.print_details()
        if args.list_latest_non_ga:
            latest_non_ga_tag = tag.get_latest_non_ga_tag()
            if latest_non_ga_tag is None:
                print(str.format('Latest non-ga tag is None'))
            else:
                print(str.format('Latest non-ga tag:'))
                latest_non_ga_tag.print_details()

    if args.test_all_tags != 'not present':
        print_unknown = args.test_all_tags != "sap" and args.test_all_tags != "jdk"
        print_sap = args.test_all_tags != "unknown" and args.test_all_tags != "jdk"
        print_jdk = args.test_all_tags != "unknown" and args.test_all_tags != "sap"
        tags = utils.get_github_tags()
        if tags is None:
            print("Could not get tags from GitHub")
            sys.exit(-1)
        for tag in tags:
            to = Tag.from_string(tag['name'])
            if to is None:
                if print_unknown:
                    print(str.format("Tag {0} is unknown.", tag['name']))
            elif to.is_sapmachine_tag():
                if print_sap:
                    to.print_details()
                    latest_non_ga = to.get_latest_non_ga_tag()
                    if latest_non_ga is None:
                        print(str.format("Latest non-ga tag for {0} is None", to.as_string()))
                        sys.exit(-1)
                    elif latest_non_ga != to:
                        print("  Latest non-ga tag:")
                        latest_non_ga.print_details(indent = '  ')
            elif to.is_jdk_tag():
                if print_jdk:
                    to.print_details()
                    latest_non_ga = to.get_latest_non_ga_tag()
                    if latest_non_ga is None:
                        print(str.format("Latest non-ga tag for {0} is None", to.as_string()))
                        sys.exit(-1)
                    elif latest_non_ga != to:
                        print("  Latest non-ga tag:")
                        latest_non_ga.print_details(indent = '  ')

    if args.jvm:
        _, std_out, std_err = utils.run_cmd([join(args.jvm, 'bin', 'java.exe'), '-version'], std=True)
        print('Stdout:')
        print(std_out)
        print('Stderr')
        print(std_err)

        version, version_part, major, version_sap, build_number = utils.sapmachine_version_components(std_err, multiline=True)
        version_components = [version, version_part, major, version_sap, build_number]
        print(' '.join([version_component if version_component else 'N/A' for version_component in version_components]))
        sapmachine_version = [e for e in version_part.split('.')]
        print(sapmachine_version)

if __name__ == "__main__":
    sys.exit(main())
