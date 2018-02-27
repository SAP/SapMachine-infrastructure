'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import argparse
import json
import utils

from os.path import join

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--srcdir', help='the source directory to copy from', metavar='DIR', required=True)
    parser.add_argument('-t', '--targetdir', help='the target directory to copy to', metavar='DIR', required=True)
    parser.add_argument('--install-plugins', help='install the Jenkins plugins', action='store_true', default=False)
    args = parser.parse_args()

    source = os.path.realpath(args.srcdir)
    target = os.path.realpath(args.targetdir)

    if not os.path.exists(target):
        os.mkdir(target)

    utils.copytree(join(source, 'jenkins_configuration'), target)

    if args.install_plugins:
        with open(join(source, 'jenkins_configuration', 'plugin_list.json'), 'r') as plugin_list_json:
            plugin_list = json.loads(plugin_list_json.read())

            install_cmd = ['/usr/local/bin/install-plugins.sh']

            for plugin in plugin_list:
                install_cmd.append(str.format('{0}:{1}', plugin['Extension-Name'], plugin['Plugin-Version']))

            utils.run_cmd(install_cmd)

if __name__ == "__main__":
    sys.exit(main())
