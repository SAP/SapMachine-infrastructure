'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils
import argparse
from urllib.request import urlopen, Request
from urllib.parse import quote
from os.path import join

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine Git tag', metavar='TAG', required=True)
    args = parser.parse_args()

    print(str(utils.sapmachine_tag_is_release(args.tag)))

if __name__ == "__main__":
    sys.exit(main())