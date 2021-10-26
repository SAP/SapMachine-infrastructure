'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import sys
from versions import SapMachineTag

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine Git tag', metavar='TAG', required=True)
    args = parser.parse_args()

    tag = SapMachineTag.from_string(args.tag)
    if tag is None:
        return -1

    print(tag.get_update())

    return 0

if __name__ == "__main__":
    sys.exit(main())
