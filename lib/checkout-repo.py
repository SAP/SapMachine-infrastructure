'''
Copyright (c) 2001-2021 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import sys
import utils
import argparse

from os.path import join

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repo', help='the repository to check out')
    parser.add_argument('-b', '--branch', help='the branch to check out')
    parser.add_argument('-t', '--target', help='the target directory')
    args = parser.parse_args()

    utils.git_clone(args.repo, args.branch, args.target)
    return 0

if __name__ == "__main__":
    sys.exit(main())
