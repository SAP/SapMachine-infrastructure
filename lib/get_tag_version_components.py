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

from urllib2 import urlopen, Request, quote
from os.path import join

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine Git tag', metavar='TAG', required=True)
    parser.add_argument('-s', '--separator', help='the separator char', metavar='SEPARATOR', required=False, default=' ')
    args = parser.parse_args()

    version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(args.tag)
    version_components = [version, version_part, major, build_number, sap_build_number, os_ext]
    print(args.separator.join([version_component if version_component else 'N/A' for version_component in version_components]))

if __name__ == "__main__":
    sys.exit(main())