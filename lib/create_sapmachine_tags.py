'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils
import argparse

from utils import JDKTag
from os.path import join

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.crumb_requester import CrumbRequester

branch_pattern = re.compile('sapmachine([\d]+)?$')
merge_commit_pattern = re.compile('Merge pull request #\d+ from SAP/pr-jdk-')

def run_jenkins_jobs(major, tag):
    if 'JENKINS_CREDENTIALS' not in os.environ:
        return

    jenkins_url = 'https://ci.sapmachine.io'
    jenkins_user = os.environ['JENKINS_CREDENTIALS_USR']
    jenkins_password = os.environ['JENKINS_CREDENTIALS_PSW']

    server = Jenkins(jenkins_url, username=jenkins_user, password=jenkins_password,
        requester=CrumbRequester(
            baseurl=jenkins_url,
            username=jenkins_user,
            password=jenkins_password
        )
    )

    build_jobs = [
        str.format('build-{0}-release-linux_x86_64', major),
        str.format('build-{0}-release-linux_ppc64le', major),
        str.format('build-{0}-release-linux_ppc64', major),
        str.format('build-{0}-release-macos_x86_64', major),
        str.format('build-{0}-release-windows_x86_64', major)
    ]

    job_params = {
        'PUBLISH': 'true' ,
        'RELEASE': 'false',
        'RUN_TESTS': 'true',
        'GIT_TAG_NAME': tag
    }

    for job in build_jobs:
        print(str.format('starting jenkins job "{0}" ...', job))
        server.build_job(job, job_params)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='the temporary working directory', metavar='DIR', default="tags_work", required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    utils.remove_if_exists(workdir)
    os.makedirs(workdir)

    # clone the SapMachine repository
    git_target_dir = join(workdir, 'sapmachine')
    utils.git_clone('github.com/SAP/SapMachine.git', 'sapmachine', git_target_dir)

    # fetch all branches
    branches = utils.github_api_request('branches', per_page=100)
    sapmachine_latest = 0
    sapmachine_branches = []

    # iterate all branches of the SapMachine repository
    for branch in branches:
        # filter for sapmachine branches
        match = branch_pattern.match(branch['name'])

        if match is not None:
            # found sapmachine branch
            if match.group(1) is not None:
                major = int(match.group(1))
                sapmachine_branches.append([branch['name'], major])
                sapmachine_latest = max(major, sapmachine_latest)
            else:
                sapmachine_branches.append([branch['name'], 0])

    sapmachine_latest += 1

    for branch in sapmachine_branches:
        if branch[1] == 0:
            branch[1] = sapmachine_latest

        major = branch[1]
        utils.run_cmd(str.format('git checkout {0}', branch[0]).split(' '), cwd=git_target_dir)

        # find the last merge commit and check wether it is a merge from the jdk branch
        _, commit_messages, _ = utils.run_cmd('git log --merges -n 50 --format=%s'.split(' '), cwd=git_target_dir, std=True, throw=False)
        _, commit_ids, _ = utils.run_cmd('git log --merges -n 50 --format=%H'.split(' '), cwd=git_target_dir, std=True, throw=False)

        if commit_messages and commit_ids:
            commit_messages = [commit_message for commit_message in commit_messages.split(os.linesep) if commit_message]
            commit_ids = [commit_id for commit_id in commit_ids.split(os.linesep) if commit_id]

        merge_commits = map(lambda x,y:[x,y],commit_messages,commit_ids)

        for merge_commit in merge_commits:
            commit_message = merge_commit[0]
            commit_id = merge_commit[1]
            match_merge_commit = re.search(merge_commit_pattern, commit_message)
            match_jdk_tag = re.search(JDKTag.jdk_tag_pattern, commit_message)

            if match_merge_commit is not None and match_jdk_tag is not None:
                print(str.format('found latest merge commit "{0}" for branch "{1}"', commit_message, branch))
                _, tags, _ = utils.run_cmd(str.format('git tag --contains {0}', commit_id).split(' '), cwd=git_target_dir, std=True, throw=False)

                if not tags:
                    # not tagged yet
                    # create sapmachine tag
                    jdk_tag = JDKTag(match_jdk_tag)
                    print(str.format('creating tag "{0}"', jdk_tag.as_sapmachine_tag()))
                    utils.run_cmd(str.format('git checkout {0}', commit_id).split(' '), cwd=git_target_dir)
                    utils.run_cmd(str.format('git tag {0}', jdk_tag.as_sapmachine_tag()).split(' '), cwd=git_target_dir)
                    utils.run_cmd(str.format('git push origin {0}', jdk_tag.as_sapmachine_tag()).split(' '), cwd=git_target_dir)
                    run_jenkins_jobs(major, jdk_tag.as_sapmachine_tag())
                else:
                    print('already tagged ...')

                break

    utils.remove_if_exists(workdir)
    return 0

if __name__ == "__main__":
    sys.exit(main())