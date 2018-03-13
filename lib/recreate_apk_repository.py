'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import argparse
import utils

from os.path import join
from os.path import realpath
from os.path import dirname
from os.path import basename

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repository', help='specify the repository directory', metavar='DIR', required=True)
    parser.add_argument('-k', '--key', help='specify the private key file', metavar='KEYFILE', required=True)
    args = parser.parse_args()

    repository = realpath(args.repository)
    keyfile = basename(args.key)
    keydir = dirname(args.key)

    cmd = str.format('apk index -o {0}/APKINDEX.tar.gz {1}/*.apk',
        repository,
        repository)
    utils.run_cmd(cmd, shell=True)

    cmd = str.format('abuild-sign -k {0}/{1} {2}/APKINDEX.tar.gz',
        keydir,
        keyfile,
        repository)
    utils.run_cmd(cmd, shell=True)

if __name__ == "__main__":
    sys.exit(main())