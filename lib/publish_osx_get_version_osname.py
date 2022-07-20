'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import sys
#quick hack: import utils. Otherwise there is a circularity when importing SapMachineTag from versions.
import utils

from versions import SapMachineTag

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine Git tag', metavar='TAG', required=True)
    args = parser.parse_args()

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        return -1

    print(str.format('{0} {1}', tag.get_version_string(), "macos" if tag.get_major() >= 17 or (tag.get_major() == 11 and tag.get_update() > 15) else "osx"))

    return 0

if __name__ == "__main__":
    sys.exit(main())
