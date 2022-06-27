'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import json
import os
import sys
import utils

from os.path import join

jenkins_configuration = 'jenkins_configuration'

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--targetdir', help='the target directory (Jenkins home directory)', metavar='DIR', required=True)
    parser.add_argument('-b', '--backuprepodir', help='the backup repository', metavar='DIR', default='SapMachine-Infrastructure')
    parser.add_argument('--install-plugins', help='install the Jenkins plugins', action='store_true', default=False)
    parser.add_argument('--plugins-only', help='install only the Jenkins plugins (implies --install-plugins)', action='store_true', default=False)
    args = parser.parse_args()

    if args.plugins_only:
        args.install_plugins = True

    source = os.path.realpath(args.backuprepodir)
    target = os.path.realpath(args.targetdir)

    if not os.path.exists(target):
        os.mkdir(target)

    if not args.plugins_only:
        utils.copytree(join(source, jenkins_configuration), target)

    if args.install_plugins:
        with open(join(source, jenkins_configuration, 'plugin_list.json'), 'r') as plugin_list_json:
            plugin_list = json.loads(plugin_list_json.read())

            install_cmd = ['/bin/jenkins-plugin-cli', '--plugins']

            for plugin in plugin_list:
                if 'Short-Name' not in plugin:
                    # In case the key is missing, print some more information before bail out
                    print("Short-Name missing for:")
                    for key in plugin:
                        print(str.format("{0}:{1}", key, plugin[key]))
                    print("")
                install_cmd.append(str.format('{0}:{1}', plugin['Short-Name'], plugin['Plugin-Version']))

            utils.run_cmd(install_cmd)

    return 0

if __name__ == "__main__":
    sys.exit(main())
