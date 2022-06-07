'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import shutil
import sys
import utils
import xml.etree.ElementTree

from utils import git_clone
from os.path import join

jenkins_configuration = 'jenkins_configuration'

def push_backup(local_repo):
    _, giturl, _ = utils.run_cmd(['git', 'config', '--get', 'remote.origin.url'], cwd=local_repo, std=True)
    credurl = str.format('https://{0}:{1}@{2}', os.environ['GIT_USER'], os.environ['GIT_PASSWORD'], giturl.rstrip().split("//")[1])
    _, branch, _ = utils.run_cmd(['git', 'branch', '--show-current'], cwd=local_repo, std=True)
    branch = branch.rstrip()

    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']

    utils.run_cmd(['git', 'add', jenkins_configuration], cwd=local_repo)
    utils.run_cmd(['git', 'commit', '-m', 'Updated Jenkins configuration.'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'pull', credurl, branch, '--rebase'], cwd=local_repo, env=env)
    utils.run_cmd(['git', 'push', credurl], cwd=local_repo, env=env)

def remove_sensitive_data(config_xml, elements):
    config = xml.etree.ElementTree.parse(config_xml)
    config_root = config.getroot()

    for e in elements:
        for private_key in config_root.iter(e):
            if private_key.text.rstrip():
                private_key.text = 'REMOVED_BY_BACKUP'

    config.write(config_xml)

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
                remove_sensitive_data(join(config_xml_target_dir, file), ['privateKey', 'password'])

def create_plugin_list(src_dir, target_dir):
    import json

    plugin_list = []

    for root, dirs, files in os.walk(join(src_dir, 'plugins'), topdown=True):
        for file in files:
            if file == 'MANIFEST.MF':
                with open(join(root, file), 'r') as manifest:
                    _lines = manifest.read().splitlines()
                    lines = []

                    for line in _lines:
                        if line.startswith(' '):
                            lines[-1] += line
                        else:
                            lines.append(line)

                    properties = {}
                    for line in lines:
                        prop = line.split(': ', 1)
                        if len(prop) == 2:
                            properties[prop[0]] = prop[1]
                    plugin_list.append(properties)

    with open(join(target_dir, 'plugin_list.json'), 'w+') as out:
        out.write(json.dumps(plugin_list, indent=4, sort_keys=True))

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--srcdir', help='the source directory (Jenkins home directory)', metavar='DIR', required=True)
    parser.add_argument('-r', '--backuprepo', help='the backup repository', metavar='REPO', default='github.com/SAP/SapMachine-infrastructure.git')
    parser.add_argument('-d', '--dryrun', help='do not push the Jenkins configuration', action='store_true', default=False)
    args = parser.parse_args()

    git_clone(args.backuprepo, "backupJenkins", "SapMachine-Backup")
    target_dir = join("SapMachine-Backup", jenkins_configuration)

    utils.remove_if_exists(target_dir)
    os.mkdir(target_dir)
    copy_configurations(args.srcdir, target_dir)
    create_plugin_list(args.srcdir, target_dir)

    if not args.dryrun:
        push_backup("SapMachine-Backup")

    return 0

if __name__ == "__main__":
    sys.exit(main())
