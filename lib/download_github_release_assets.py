"""
Copyright (c) 2024 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
"""

import argparse
import sys
import tempfile

from utils import download_github_release_assets


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='MAJOR', required=True)
    parser.add_argument('-g', '--github-api', default='https://api.github.com', help='the target github api url',
                        metavar='GITHUB', required=False)
    parser.add_argument('-o', '--github-org', default='SAP', help='the github org', metavar='ORG', required=False)
    parser.add_argument('-r', '--github-repo', default='SapMachine', help='the github repo', metavar='REPO',
                        required=False)
    args = parser.parse_args(argv)

    tempdir = tempfile.mkdtemp(prefix="download-", dir=".")

    download_github_release_assets(release_name=args.tag, api=args.github_api, org=args.github_org,
                                   repo=args.github_repo, destination=tempdir)
    print(tempdir)
    return 1


if __name__ == "__main__":
    main(sys.argv[1:])
