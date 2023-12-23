'''
Copyright (c) 2018-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import json
import os
import sys
import utils

from os.path import join
from versions import Tag, SapMachineTag

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='Test a tag', metavar='TAG')
    parser.add_argument('-l', '--list-latest-non-ga', default=False, help='List the latest non-ga tag', action='store_true')
    parser.add_argument('-a', '--test-all-tags', nargs='?', default='not present', const='all', help='List latest tags, value could be sap,jdk,unknown')
    parser.add_argument('-r', '--test-all-releases', default=False, help='List latest releases', action='store_true')
    parser.add_argument('-v', '--jvm', help='Test a VM', metavar='VM Path')
    parser.add_argument('-s', '--version-string', help='Test a VM version String', metavar='Version String')
    parser.add_argument('-i', '--input', choices=['github', 'file'], default='github', help='input source, can be either "github" or "file". Default is "github". For "file", an input file is needed that contains the results of the GitHub Release API call in json format. The default name would be "github-releases.json" and can be modified with option "--input-file"', metavar='INPUT_SOURCE')
    parser.add_argument('--github-data-file', default='github-releases.json', help='input file that contains the results of the GitHub Release API call in json format (optional). Default: "github-releases.json"', metavar='DATA_FILE')
    parser.add_argument('--store-github-data', action='store_true', help='stores queried GitHub data in DATA_FILE')
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

    if args.test_all_releases:
        if args.input == 'github':
            # Load input data from GitHub and store to file
            print("Querying GitHub API...")
            releases = utils.github_api_request('releases', per_page=300)
            if args.store_github_data:
                print(f"Storing results to {args.github_data_file}...")
                with open(args.github_data_file, 'bw') as output_file:
                    output_file.write(json.dumps(releases, indent=2).encode('utf-8'))
        else:
            # Load input data from file
            print(f"Data Source: {args.github_data_file}.")
            if not os.path.exists(args.github_data_file):
                print(f"File {args.github_data_file} does not exist.")
                sys.exit(-1)
            with open(args.github_data_file, 'r') as file:
                releases = json.load(file)

        if releases is None:
            print("Could not get releases from GitHub")
            sys.exit(-1)

        count, release_count = 0, 0
        for release in releases:
            count += 1
            if release['prerelease'] is not True:
                release_count += 1
            t = SapMachineTag.from_string(release['name'])
            if t is None:
                print(str.format("Release {0} is unknown.", release['name']))
            else:
                t.print_details()

        print(str.format("Counted {0} releases, {1} of them are marked GA.", count, release_count))

    if args.jvm:
        _, std_out, std_err = utils.run_cmd([join(args.jvm, 'bin', 'java.exe'), '-version'], std=True)
        print('Stdout:')
        print(std_out)
        print('Stderr')
        print(std_err)

        version, major = utils.sapmachine_version_components(std_err)
        version_components = [version, major]
        print(' '.join([version_component if version_component else 'N/A' for version_component in version_components]))
        sapmachine_version = [e for e in version.split('.')]
        print(sapmachine_version)

    if args.version_string:
        print(str.format("Version string to test: \"{0}\".", args.version_string))

        version, major = utils.sapmachine_version_components(args.version_string)
        version_components = [version, major]
        print(' '.join([version_component if version_component else 'N/A' for version_component in version_components]))
        sapmachine_version = [e for e in version.split('.')]
        print(sapmachine_version)

    return 0

if __name__ == "__main__":
    sys.exit(main())
