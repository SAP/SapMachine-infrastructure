'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import argparse
import datetime
import utils

from os import remove
from os.path import join
from os.path import exists

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repository', help='specify the repository directory', metavar='DIR', required=True)
    args = parser.parse_args()

    repository = args.repository

    if exists('Packages'):
        remove('Packages')

    if exists('Packages.gz'):
        remove('Packages.gz')

    if exists('Source'):
        remove('Source')

    retcode, out, err = utils.run_cmd(['dpkg-scanpackages', '.', '/dev/null'], cwd=repository, std=True)

    with open(join(repository, 'Packages'), 'w+') as packages_file:
        packages_file.write(out)

    utils.make_gz_archive(join(repository, 'Packages'), join(repository, 'Packages.gz'))

    retcode, out, err = utils.run_cmd(['md5sum', 'Packages'], cwd=repository, std=True)
    packages_md5sum = out.split(' ')[0]
    retcode, out, err = utils.run_cmd(['sha1sum', 'Packages'], cwd=repository, std=True)
    packages_sha1sum = out.split(' ')[0]
    retcode, out, err = utils.run_cmd(['sha256sum', 'Packages'], cwd=repository, std=True)
    packages_sha256sum = out.split(' ')[0]
    retcode, out, err = utils.run_cmd(['sha512sum', 'Packages'], cwd=repository, std=True)
    packages_sha512sum = out.split(' ')[0]

    retcode, out, err = utils.run_cmd(['md5sum', 'Packages.gz'], cwd=repository, std=True)
    packages_gz_md5sum = out.split(' ')[0]
    retcode, out, err = utils.run_cmd(['sha1sum', 'Packages.gz'], cwd=repository, std=True)
    packages_gz_sha1sum = out.split(' ')[0]
    retcode, out, err = utils.run_cmd(['sha256sum', 'Packages.gz'], cwd=repository, std=True)
    packages_gz_sha256sum = out.split(' ')[0]
    retcode, out, err = utils.run_cmd(['sha512sum', 'Packages.gz'], cwd=repository, std=True)
    packages_gz_sha512sum = out.split(' ')[0]

    packages_size = os.path.getsize(join(repository, 'Packages'))
    packages_gz_size = os.path.getsize(join(repository, 'Packages.gz'))

    now = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    with open(join(repository, 'Source'), 'w+') as source_file:
        source_file.write(str.format('Date: {0}\n', now))
        source_file.write('MD5Sum:\n')
        source_file.write(str.format(' {0} {1:>16s} Packages.gz\n', packages_gz_md5sum, str(packages_gz_size)))
        source_file.write(str.format(' {0} {1:>16s} Packages\n', packages_md5sum, str(packages_size)))
        source_file.write('SHA1:\n')
        source_file.write(str.format(' {0} {1:>16s} Packages.gz\n', packages_gz_sha1sum, str(packages_gz_size)))
        source_file.write(str.format(' {0} {1:>16s} Packages\n', packages_sha1sum, str(packages_size)))
        source_file.write('SHA256:\n')
        source_file.write(str.format(' {0} {1:>16s} Packages.gz\n', packages_gz_sha256sum, str(packages_gz_size)))
        source_file.write(str.format(' {0} {1:>16s} Packages\n', packages_sha256sum, str(packages_size)))
        source_file.write('SHA512:\n')
        source_file.write(str.format(' {0} {1:>16s} Packages.gz\n', packages_gz_sha512sum, str(packages_gz_size)))
        source_file.write(str.format(' {0} {1:>16s} Packages\n', packages_sha512sum, str(packages_size)))
        source_file.write('\n')

if __name__ == "__main__":
    sys.exit(main())
