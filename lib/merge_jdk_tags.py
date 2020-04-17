'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import re
import sys
import utils
from os.path import join
from versions import JDKTag

branch_pattern = re.compile('sapmachine([\d]+)?$')

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='the temporary working directory', metavar='DIR', default="tags_work", required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    utils.remove_if_exists(workdir)
    os.makedirs(workdir)

    # fetch all branches
    sapmachine_branches = utils.get_active_sapmachine_branches()

    # fetch all tags
    tags = utils.get_github_tags()

    # iterate all tags to find the latest jdk tag for a JDK major release
    jdk_tags = {}
    for tag in tags:
        # filter for jdk tags
        jdk_tag = JDKTag.from_string(tag['name'])
        if jdk_tag is None:
            continue

        # only remember the latest jdk tag (version comparison)
        # filter out jdk update tags with build number "0" like jdk-11.0.3+0
        if ((jdk_tag.get_major() not in jdk_tags or jdk_tag.is_greater_than(jdk_tags[jdk_tag.get_major()])) and
            not (jdk_tag.get_update() > 0 and (jdk_tag.get_build_number() if jdk_tag.get_build_number() is not None else 0) == 0)):
            jdk_tags[jdk_tag.get_major()] = jdk_tag

    # clone the SapMachine repository
    git_target_dir = join(workdir, 'sapmachine')
    utils.git_clone('github.com/SAP/SapMachine.git', 'sapmachine', git_target_dir)

    # for each "sapmachine" branch, check whether it contains the latest jdk tag with matching major version
    for sapmachine_branch in sapmachine_branches:
        # get the latest jdk tag for this major version
        latest_tag = jdk_tags[sapmachine_branch[1]]

        print(str.format('latest tag for branch "{0}" is "{1}"', sapmachine_branch, latest_tag.as_string()))

        # check whether the jdk tag is already contained in the sapmachine branch
        _, out, _ = utils.run_cmd(str.format('git branch -a --contains tags/{0}', latest_tag.as_string()).split(' '), cwd=git_target_dir, std=True, throw=False)
        containing_branches_pattern = re.compile('{0}|pr-jdk-{1}.*'.format(sapmachine_branch[0], sapmachine_branch[1]))
        match = re.search(containing_branches_pattern, out)

        if match is None:
            # the jdk tag is not contained in a sapmachine branch
            # create a pull request branch and a pull request.
            print(str.format('creating pull request "pr-{0}" with base branch "{1}"', latest_tag.as_string(), sapmachine_branch))
            utils.run_cmd(str.format('git checkout {0}', latest_tag.as_string()).split(' '), cwd=git_target_dir)
            utils.run_cmd(str.format('git checkout -b pr-{0}', latest_tag.as_string()).split(' '), cwd=git_target_dir)
            utils.run_cmd(str.format('git push origin pr-{0}', latest_tag.as_string()).split(' '), cwd=git_target_dir)

            pull_request = str.format('{{ "title": "Merge to tag {0}", "body": "please pull", "head": "pr-{1}", "base": "{2}" }}',
                latest_tag.as_string(), latest_tag.as_string(), sapmachine_branch[0])

            utils.github_api_request('pulls', data=pull_request, method='POST')

    utils.remove_if_exists(workdir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
