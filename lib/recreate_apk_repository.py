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
    parser.add_argument('-d', '--docker', help='specify the docker file directory', metavar='DIR', required=True)
    parser.add_argument('-k', '--key', help='specify the private key file', metavar='KEYFILE', required=True)
    args = parser.parse_args()

    repository = realpath(args.repository)
    docker_dir = args.docker
    keyfile = basename(args.key)
    keydir = dirname(args.key)
    docker_container_name = 'alpine:recreate_apk_repository'

    utils.run_cmd(['docker', 'build', '-t' , docker_container_name, docker_dir])
    docker_run_cmd = str.format('apk index -o /apk_repo/APKINDEX.tar.gz /apk_repo/*.apk && abuild-sign -k /apk_keys/{0} /apk_repo/APKINDEX.tar.gz', keyfile)
    docker_run_args = ['docker', 'run',
        '-v', str.format('{0}:/apk_repo:rw,z', repository),
        '-v', str.format('{0}:/apk_keys:ro,z', keydir),
        '-t', docker_container_name, 'bash', '-lic', docker_run_cmd]
    utils.run_cmd(docker_run_args)

if __name__ == "__main__":
    sys.exit(main())