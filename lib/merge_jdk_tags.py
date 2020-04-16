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

branch_pattern = re.compile('sapmachine([\d]+)?$')

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='the temporary working directory', metavar='DIR', default="tags_work", required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    utils.remove_if_exists(workdir)
    os.makedirs(workdir)

    # fetch all branches
    sapmachine_branches = utils.get_sapmachine_branches()

    # fetch all tags
    jdk_tags = {}
    tags = utils.get_github_tags()

    # iterate all tags
    for tag in tags:
        # filter for jdk tags
        match = JDKTag.jdk_tag_pattern.match(tag['name'])

        if match is not None:
            # found a jdk tag
            jdk_tag = JDKTag(match)
            major = jdk_tag.get_major()

            # only store the latest jdk tag (version comparison)
            if  major not in jdk_tags or jdk_tag.is_greater_than(jdk_tags[major]):
                # filter jdk update tags with build number "0" like jdk-11.0.3+0
                if not (jdk_tag.is_update() and jdk_tag.get_build_number() == 0):
                    jdk_tags[major] = jdk_tag


    # clone the SapMachine repository
    git_target_dir = join(workdir, 'sapmachine')
    utils.git_clone('github.com/SAP/SapMachine.git', 'sapmachine', git_target_dir)

    # for each "sapmachine" branch, check whether it contains the latest jdk tag with matching major version
    for sapmachine_branch in sapmachine_branches:
        # get the latest jdk tag for this major version
        latest_tag_for_branch = jdk_tags[sapmachine_branch[1]]

        print(str.format('latest tag for branch "{0}" is "{1}"', sapmachine_branch, latest_tag_for_branch.as_string()))

        # check whether the jdk tag is already contained in the sapmachine branch
        _, out, _ = utils.run_cmd(str.format('git branch -a --contains tags/{0}', latest_tag_for_branch.as_string()).split(' '), cwd=git_target_dir, std=True, throw=False)
        containing_branches_pattern = re.compile('{0}|pr-jdk-{1}.*'.format(sapmachine_branch[0], sapmachine_branch[1]))
        match = re.search(containing_branches_pattern, out)

        if match is None:
            # the jdk tag is not contained in a sapmachine branch
            # create a pull request branch and a pull request.
            print(str.format('creating pull request "pr-{0}" with base branch "{1}"', latest_tag_for_branch.as_string(), sapmachine_branch))
            utils.run_cmd(str.format('git checkout {0}', latest_tag_for_branch.as_string()).split(' '), cwd=git_target_dir)
            utils.run_cmd(str.format('git checkout -b pr-{0}', latest_tag_for_branch.as_string()).split(' '), cwd=git_target_dir)
            utils.run_cmd(str.format('git push origin pr-{0}', latest_tag_for_branch.as_string()).split(' '), cwd=git_target_dir)

            pull_request = str.format('{{ "title": "Merge to tag {0}", "body": "please pull", "head": "pr-{1}", "base": "{2}" }}',
                latest_tag_for_branch.as_string(),
                latest_tag_for_branch.as_string(),
                sapmachine_branch[0])

            utils.github_api_request('pulls', data=pull_request, method='POST')

    utils.remove_if_exists(workdir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
