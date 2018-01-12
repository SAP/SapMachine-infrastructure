'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import argparse
import tempfile
import utils

from os.path import join

git_user = os.environ['GIT_USER']
git_password = os.environ['GIT_PASSWORD']
repo = str.format('https://{0}:{1}@github.com/SAP/SapMachine-infrastructure.git', git_user, git_password)
branch = 'master'
jenkins_configuration = 'jenkins_configuration'

def clone_sapmachine_infra(target):
    utils.run_cmd(['git', 'clone', '-b', branch, repo, target])

def push_sapmachine_infra(local_repo):
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']
    utils.run_cmd(['git', 'add', jenkins_configuration], cwd=local_repo)
    utils.run_cmd(['git', 'commit', '-m', 'Updated Jenkins configuration.'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'fetch'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'rebase'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'push'], cwd=local_repo, env=env)

def copy_configurations(src_dir, target_dir):
    exclude_dirs = ['users', 'secrets', 'workspace', '.cache', 'caches', 'logs', 'plugins', 'fingerprints']
    exclude_files = ['credentials.xml']

    for root, dirs, files in os.walk(src_dir, topdown=True):
        path_elements = os.path.relpath(root, start=src_dir).split(os.path.sep)

        if len(path_elements) > 0:
            if ((path_elements[0] in exclude_dirs) or
               (path_elements[0] == 'jobs' and 'builds' in path_elements)):
                dirs[:] = []
                files[:] = []
                continue

        for file in files:
            if file.endswith('.xml') and file not in exclude_files:
                config_xml = join(root, file)
                config_xml_path = os.path.relpath(config_xml, start=src_dir)
                config_xml_dir = os.path.dirname(config_xml_path)
                config_xml_target_dir = join(target_dir, config_xml_dir)

                print(str.format('found configuration "{0}"', config_xml))

                #print(str.format('config_xml="{0}"\nconfig_xml_path="{1}"\nconfig_xml_dir="{2}"\ntarget_dir="{3}"\n\n',
                #    config_xml,
                #    config_xml_path,
                #    config_xml_dir,
                #    config_xml_target_dir))

                if not os.path.exists(config_xml_target_dir):
                    os.makedirs(config_xml_target_dir)

                shutil.copy(config_xml, config_xml_target_dir)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--srcdir', help='the Jenkins home directory', metavar='DIR', required=True)
    parser.add_argument('-d', '--dryrun', help='do not push the Jenkins configuration', action='store_true', default=False)
    parser.add_argument('--keepworkdir', help='do not delete the temporary work directory', action='store_true', default=False)
    args = parser.parse_args()

    src_dir = args.srcdir
    git_dir = tempfile.mkdtemp()
    target_dir = join(git_dir, jenkins_configuration)

    utils.remove_if_exists(git_dir)
    clone_sapmachine_infra(git_dir)
    utils.remove_if_exists(target_dir)
    os.mkdir(target_dir)
    copy_configurations(src_dir, target_dir)

    if not args.dryrun:
        push_sapmachine_infra(git_dir)

    if not args.keepworkdir:
        utils.remove_if_exists(git_dir)

if __name__ == "__main__":
    sys.exit(main())