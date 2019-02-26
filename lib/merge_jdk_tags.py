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

from os.path import join

jdk_tag_pattern = re.compile('jdk-((\d+)(\.\d+)*)(\+\d+|-ga)$')

class JDKTag:
    def __init__(self, match):
        self.tag = match.group(0)
        self.version = match.group(1).split('.')
        self.build_number = match.group(4)[1:]
        self.is_ga = self.build_number == 'ga'

        if self.is_ga:
            self.build_number = 999999
        else:
            self.build_number = int(self.build_number)

        self.version = map(int, self.version)
        self.version.extend([0 for i in range(3 - len(self.version))])

    def as_string(self):
        return self.tag

    def get_version(self):
        return self.version

    def get_major(self):
        return self.version[0]

    def get_build_number(self):
        return self.build_number

    def is_ga(self):
        return self.is_ga

    def is_greater_than(self, other):
        ts = tuple(self.version)
        to = tuple(other.get_version())
        ts += (self.build_number,)
        to += (other.get_build_number(),)
        return ts > to


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='the temporary working directory', metavar='DIR', default="tags_work", required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    #utils.remove_if_exists(workdir)
    #os.makedirs(workdir)

    sapmachine_latest = 0
    sapmachine_branches = []
    branch_pattern = re.compile('sapmachine([\d]+)?$')
    branches = utils.github_api_request('branches')

    for branch in branches:
        match = branch_pattern.match(branch['name'])

        if match is not None:
            if match.group(1) is not None:
                major = int(match.group(1))
                sapmachine_branches.append([branch['name'], major])
                sapmachine_latest = max(sapmachine_latest, major)
            else:
                sapmachine_branches.append([branch['name'], 0])

    sapmachine_latest += 1

    for sapmachine_branch in sapmachine_branches:
        if sapmachine_branch[1] is 0:
            sapmachine_branch[1] = sapmachine_latest

    jdk_tags = {}
    tags = utils.github_api_request('tags', per_page=300)

    for tag in tags:
        match = jdk_tag_pattern.match(tag['name'])

        if match is not None:
            jdk_tag= JDKTag(match)
            major = jdk_tag.get_major()

            if  major not in jdk_tags or jdk_tag.is_greater_than(jdk_tags[major]):
                jdk_tags[major] = jdk_tag

    git_target_dir = join(workdir, 'sapmachine')
    #utils.git_clone('github.com/SAP/SapMachine.git', 'sapmachine', git_target_dir)

    for sapmachine_branch in sapmachine_branches:
        latest_tag_for_branch = jdk_tags[sapmachine_branch[1]]

        #utils.run_cmd(str.format('git checkout {0}', sapmachine_branch[0]).split(' '), cwd=git_target_dir)
        _, out, _ = utils.run_cmd(str.format('git branch -a --contains tags/{0}', latest_tag_for_branch.as_string()).split(' '), cwd=git_target_dir, std=True)
        print(out)

    #utils.remove_if_exists(workdir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
