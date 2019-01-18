import os
import sys
import json
import re
import utils
import argparse

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='TAG', required=True)
    args = parser.parse_args()

    tag = args.tag

    version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(tag)

    print(str.format('version: {0}, version_part: {1}, major: {2}, build_number: {3}, sap_build_number: {4}, os_ext: {5}',
        version, version_part, major, build_number, sap_build_number, os_ext))

if __name__ == "__main__":
    sys.exit(main())