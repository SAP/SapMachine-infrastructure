'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import argparse
import tempfile
import json
import utils

from os.path import join

git_user = os.environ['GIT_USER']
git_password = os.environ['GIT_PASSWORD']
repo = str.format('https://{0}:{1}@github.com/SAP/SapMachine-infrastructure.git', git_user, git_password)
branch = 'master'
jenkins_configuration = 'jenkins_configuration'

def clone_sapmachine_infra(target):
    utils.run_cmd(['git', 'clone', '-b', branch, repo, target])

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--targetdir', help='the target directory to copy to', metavar='DIR', required=True)
    parser.add_argument('--jenkins-url', help='the target directory to copy to', metavar='DIR', required=False)
    args = parser.parse_args()

    git_dir = tempfile.mkdtemp()
    target = args.targetdir

    if not os.path.exists(target):
        os.mkdir(target)

    clone_sapmachine_infra(git_dir)
    utils.copytree(join(git_dir, jenkins_configuration), target)

    jenkins_url = args.jenkins_url

    if jenkins_url is not None:
        utils.download_artifact(jenkins_url + '/jnlpJars/jenkins-cli.jar', join(git_dir, 'jenkins-cli.jar'))

        with open(join(git_dir, jenkins_configuration, 'plugin_list.json'), 'r') as plugin_list_json:
            plugin_list = json.loads(plugin_list_json.read())

            for plugin in plugin_list:
                utils.run_cmd(['java', '-jar', join(git_dir, 'jenkins-cli.jar'), '-s', jenkins_url, 'install-plugin', plugin['Short-Name']])

    utils.remove_if_exists(git_dir)

if __name__ == "__main__":
    sys.exit(main())
